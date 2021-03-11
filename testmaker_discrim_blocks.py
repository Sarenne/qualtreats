
# import argparse
import copy
import glob
import json
import requests

from string import Template
from collections import OrderedDict

import config

from discriminative_turn_utils import *

""""""

##### Define global params #####
# Input and output json objects for qualtrics survey
JSON_TEMPLATE = "template_blocks.json"
SAVE_TEMPLATE = "output_survey_templates/full_swb/blocks"

NUM_QUESTIONS = 20
REPEATS = 1

# audio templates should not be changed
AUDIO_HTML_TEMPLATE = "audio_template.html"
PLAY_BUTTON = "play_button.html"

# Where data is stored
# BASE_PATH ='/group/project/cstr3/html/sarenne/test_qualtrics/' # where generated experiment datas are stored
# BASE_URL = 'https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/'
BASE_EXT = 'sarenne/qualtrics_full/'
BASE_PATH = f'/afs/inf.ed.ac.uk/group/cstr/datawww/{BASE_EXT}'
BASE_URL = f'https://data.cstr.ed.ac.uk/{BASE_EXT}'
URLS_PATH = 'discrim_turn_resources/urls.json'

##### Define global methods #####
# load JSON template from file
def get_basis_json():
    with open(JSON_TEMPLATE) as json_file:
        return json.load(json_file)

# standard audio player for all question types except MUSHRA
def get_player_html(url):
    with open(AUDIO_HTML_TEMPLATE) as html_file:
        return Template(html_file.read()).substitute(url=url)

def path_to_url(path):
    """Convert path to group.inf.ed.ac.uk data to url"""
    pass

# audio player with only play/pause controls for MUSHRA tests
# to prevent participants identifying hidden reference by duration
def get_play_button(url, n): # player n associates play button with a specific audio
    with open(PLAY_BUTTON) as html_file:
        return Template(html_file.read()).substitute(url=url, player=n)

def q_set_up(q_id, export_id, basis_question):
    """Init a template and fill with generic attributes (survey ID) and basic question attributes (q ID)"""
    # Get template
    new_q = copy.deepcopy(basis_question)
    # Update the survey ID
    new_q['SurveyID'] = config.survey_id
    # Update question ID and related fields
    new_q['Payload'].update({'QuestionID' : f'QID{q_id}',
                             'DataExportTag' : f'{export_id}',
                             'QuestionDescription' : f'Q{q_id}',
                             })
    new_q.update({'PrimaryAttribute' : f'QID{q_id}',
                  'SecondaryAttribute' : f'QID{q_id}'})
    return new_q, f'QID{q_id}'

def make_discrim_question_set(q_counter, experiment_id, audio_urls, context_conditions, context_ids, basis_question):
    """

    Args
        q_counter (int): to track the question ids for qualtrics "QuestionID" attribute (used as the ID of the first
            question round in discrim set)
        experiment_id (str): the dir_name of the experiment (identifier of conv_id, utter_d, seeds, correct_indx)
        audio_urls (list): list of str urls
        contexts ():
        basis_question ():
    """

    def update_choices(q_json, audio_urls, individual=False):
        """Fill matrix with audio samples for a particular experiment. Return updated question template object"""

        indv_urls = [f for f in audio_urls if f.split("/")[-1][-8:-4]=='indv']
        if individual:
            urls = indv_urls
        else:
            urls = list(set(audio_urls) - set(indv_urls))

        choice_template = q_json['Payload']['Choices']['1']# make choice template
        # empty 'Choices' so flexible number can be added using Choice template
        q_json['Payload']['Choices'] = {}
        for audio in urls:
            indx = int(audio.split('/')[-1][0])
            choice = copy.deepcopy(choice_template)
            choice['Display'] = get_player_html(audio) # add audio player as choice
            q_json['Payload']['Choices'][str(indx+1)] = choice
        return q_json

    def update_text(q_json, speaker_turns, utter_id, turns_before, turns_after, individual=False):
        """Fill in question text with the conversation context. Return updated question template object"""

        q_content = context_print(utter_id, speaker_turns, turns_before, turns_after, individual=individual)
        q_text = discrim_question_print(q_content)
        q_json['Payload'].update({'QuestionText': q_text})
        return q_json

    # Load the conversation and build speaker turns
    # conversation = json.loads(requests.get(BASE_URL + experiment_id + '/conversation.json').text)
    # conversation = requests.get(BASE_URL + experiment_id + '/conversation.json').json()

    with open(BASE_PATH + experiment_id + '/conversation.json') as jfs:
        conversation = json.load(jfs)
    if experiment_id[-3] in ['M', 'F']: # check for gender in string
        utter_id = int(experiment_id.split("_")[-5])
    else:
        utter_id = int(experiment_id.split("_")[-4])
    speaker_turns = make_speaker_turns(conversation)

    # Store the question set  (NOTE should this be a list?)
    q_set = []
    q_exports = []

    for i, cntxt_id in enumerate(context_ids):

        (before, after), indiv = context_conditions[cntxt_id]

        # Generate a discrim turn experiment
        q_export = f'C{cntxt_id}_' + experiment_id
        new_q, ques_id = q_set_up(q_counter + i + 1, q_export, basis_question)

        # Fill template with audio choices and text
        new_q = update_choices(new_q, audio_urls, individual=indiv)
        new_q = update_text(new_q, speaker_turns, utter_id, before, after, individual=indiv)
        q_set.append(new_q)
        q_exports.append((q_export, ques_id))

    return q_set, q_exports


def make_gender_question(q_counter, experiment_id, basis_question):
    """

    Args
        q_counter (int): to track the question ids for qualtrics "QuestionID" attribute (used as the ID of the first
            question round in discrim set)
        experiment_id (str): the dir_name of the experiment (identifier of conv_id, utter_d, seeds, correct_indx)
        audio_urls (list): list of str urls
        contexts ():
        basis_question ():
    """

    def update_text(q_json, speaker_turns, utter_id):
        """Fill in question text with the conversation context. Return updated question template object"""

        q_content = context_print(utter_id, speaker_turns, 0, -1)
        q_text = gender_question_print(q_content)
        q_json['Payload'].update({'QuestionText': q_text})
        return q_json

    # Load the conversation and build speaker turns
    # conversation = json.loads(requests.get(BASE_URL + experiment_id + '/conversation.json').text)
    # conversation = requests.get(BASE_URL + experiment_id + '/conversation.json').json()
    with open(BASE_PATH + experiment_id + '/conversation.json') as jfs:
        conversation = json.load(jfs)
    utter_id = int(experiment_id.split("_")[-5]) # check for gender in string
    speaker_turns = make_speaker_turns(conversation)

    # Store the question set  (NOTE should this be a list?)
    q_set = []
    q_exports = []

    # Generate a gender check question
    q_export = f'G_' + experiment_id
    new_q, ques_id = q_set_up(q_counter + 1, q_export, basis_question)

    # Fill template with audio choices and text
    new_q = update_text(new_q, speaker_turns, utter_id)
    q_set.append(new_q)
    q_exports.append((q_export, ques_id))

    return q_set, q_exports

def block_set_up(block_template, block_id, quest_ids):
    """block_template is a dict (type, description, ID, blockelements, options)"""

    # new_block = block_template.copy()
    new_block = OrderedDict()
    new_block["Type"] = 'Standard'
    new_block["SubType"] = ""
    new_block["Description"] = f'{block_id} Block'
    new_block["ID"] = block_id
    new_block["BlockElements"] = [] # start with empty list and fill question question ids
    for q_tag, q_id in quest_ids:
        block_element = OrderedDict()
        block_element['Type'] = 'Question'
        block_element['QuestionID'] = q_id
        new_block["BlockElements"].append(block_element)
        new_block["BlockElements"].append({"Type": "Page Break"})
    new_block["Options"] = OrderedDict({
      "BlockLocking": "false",
      "RandomizeQuestions": "false",
      "BlockVisibility": "Collapsed"})
    return new_block

# make n new blocks according to the survey_length
def make_blocks(block_ids, basis_blocks): # this could be a dict of block id: question ids (for the gender questions))
    """
    NOTE this makes new blocks now, by adding blocks (grouped questions) to elements "Survey Blocks" #
    """
    new_blocks = basis_blocks.copy() # "Survey Blocks"
    block_elements = new_blocks['Payload'].copy() # TODO just have the intro block in the template (the payload list)
    block_template = block_elements[0].copy() # use the intro block as a templat
    # for i in range(blocks_before, len(block_ids) + blocks_before + 1): # Q1,2 are already loaded from template
    for b_id, quest_ids in block_ids.items():
        new_block = block_set_up(block_template, b_id, quest_ids)
        block_elements.append(new_block)

    new_blocks['Payload'] = block_elements
    return new_blocks

def flow_set_up(block_id, flow_id):
    """flow element is a dict (type, ID (block_id), FlowID, autofill)"""
    flow_element = OrderedDict()
    flow_element['Type'] =  'Standard'
    flow_element['ID'] = block_id
    flow_element['FlowID'] = "FL_" + str(flow_id)
    flow_element['Autofill'] = []
    return flow_element

def make_flow(block_ids, basis_flow, flow_id_before=4):
    """TODO template flow should have the BlockRandomizer in it already to be added to."""
    new_flow = basis_flow # "Survey Blocks"
    flow_elements = new_flow['Payload'] # TODO just have the intro block in the template (the payload list)
    randomizer_flow = []
    for i, block_id in enumerate(block_ids):
        flow_element = flow_set_up(block_id, i + flow_id_before)
        randomizer_flow.append(flow_element)

    new_flow['Payload']['Flow'][1]['Flow'] = randomizer_flow
    return new_flow

# sets the survey ID for any object which needs it
def set_id(obj):
    obj['SurveyID'] = config.survey_id
    return obj

def main():
    """
    Given a json file (URLS_PATH in the form {experiment_id: urls}), contruct a qualtrics survey. Order of questions
    will match the order in the json file. Each question is stored with an export identifier that links it its
    experiment generation.
    """
    # parser = argparse.ArgumentParser() # add question types
    # parser.add_argument("-ab", action='store_true',
    #                     help="make A/B questions (like preference test)")
    # parser.add_argument("-abc", action='store_true',
    #                     help="make A/B/C questions (like preference test)")
    # parser.add_argument("-mc", action='store_true',
    #                     help="make multiple choice questions"
    #                     "(like error detection)")
    # parser.add_argument("-trs", action='store_true',
    #                     help="make transcription questions (with text field)")
    # parser.add_argument("-mushra", action='store_true',
    #                     help="make MUSHRA questions with sliders")
    # parser.add_argument("-mos", action='store_true',
    #                     help="make Mean Opinion Score questions with sliders")
    #
    # args = parser.parse_args()
    #
    # # get only args which were specified on command line
    # args = [key for key, value in vars(args).items() if value==True]

    # Args for experiment writing
    with open(URLS_PATH) as fs:
        experiment_urls = json.load(fs)
    # context_conditions = [((0,0), True), ((0,0), False), ((2,0), False), ((5,0), False), ((5,5), False)]
    context_conditions = [((0,0), True), ((0,0), False),
                          ((3,0), True), ((3,0), False),
                          ((6,0), True), ((6,0), False),
                          ((3,3), True), ((3,3), False),
                          ]

    survey_structures = assign_surveys(list(experiment_urls.keys()), list(range(len(context_conditions))), REPEATS, write=False)
    #
    import IPython
    IPython.embed()

    for survey_id, structure in survey_structures.items():

        # get json to use as basis for new questions
        basis_json = get_basis_json()
        elements = basis_json['SurveyElements']

        # Set the survey ID in all survey_elements
        elements = list(map(set_id, elements))

        # get basic survey components from elements JSON
        basis_blocks = elements[0] # "Survey Blocks"
        basis_flow = elements[1]
        rs = elements[2]
        basis_survey_count = elements[7] #  'Survey Question Count'

        # create list to store generated question blocks
        questions = []
        question_ids = []
        block_ids = {}
        # create counters to use when indexing optional lists
        q_counter = 2 # qualtrics question numbering starts at 1 (and first 'questions' are ethics + the intro)

        for i, (exp_id, context_id) in enumerate(structure.items()):

            quest_ids = []

            new_qs, ids = make_discrim_question_set(q_counter=q_counter+1,
                                                    experiment_id=exp_id,
                                                    audio_urls=experiment_urls[exp_id],
                                                    context_conditions=context_conditions,
                                                    context_ids=[context_id,],
                                                    basis_question=elements[-1]
                                                    )
            questions.extend(new_qs)
            question_ids.extend(ids)
            quest_ids.extend(ids)
            q_counter += len(new_qs)

            # Generate a gender question IF not indiv context condition and there is gender information (ie, gender is in the experiment ID)
            has_prosody = not(context_conditions[context_id][1])
            has_gender = exp_id[-3] in ['M', 'F']
            if has_prosody and has_gender:
                new_qs, ids = make_gender_question(q_counter=q_counter+1,
                                                   experiment_id=exp_id,
                                                   basis_question=elements[-2]
                                                  )
                questions.extend(new_qs)
                question_ids.extend(ids)
                quest_ids.extend(ids)
                q_counter += len(new_qs)

            block_ids[f"BL_{i + 2}"] = quest_ids # index from 2, as first block is the intro block
            # print(block_ids)

        # survey_length is determined by number of questions created
        survey_length = q_counter

        # Create all the items in survey elements, with helper function where doing so is not trivial
        blocks = make_blocks(block_ids, basis_blocks)
        flow = make_flow(block_ids, basis_flow)
        flow['Payload']['Properties']['Count'] = survey_length # TODO not sure if this is num questions or num flow elements (same as survey_count), otherwise update it in make flow
        flow['Payload']['Flow'][1]['SubSet'] = NUM_QUESTIONS

        # import IPython
        # IPython.embed()

        survey_count = basis_survey_count
        survey_count['SecondaryAttribute'] = str(survey_length)
        # add all the created elements together
        out_elements = [blocks, flow] + elements[2:10] + questions  # elements[8] is the ethics. elements[9] is intro

        # Add the elements to the full survey
        # Not strictly necessary as we didn't do deep copies of elements
        out_json = basis_json
        out_json['SurveyElements'] = out_elements

        # Save survey
        print(f'Generated survey {survey_id} with {survey_length} questions')
        with open(SAVE_TEMPLATE + f'_{survey_id}.qsf', 'w+') as outfile:
            json.dump(out_json, outfile, indent=4)

        # Save participant assignments
        with open(SAVE_TEMPLATE + f'_assignments.json', 'w+') as outfile:
            json.dump(survey_structures, outfile)

if __name__ == "__main__":
    main()
