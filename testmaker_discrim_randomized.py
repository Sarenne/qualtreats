
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
JSON_TEMPLATE = "template_discrim.json"
SAVE_TEMPLATE = "output_survey_templates/test/discrim"


# audio templates should not be changed
AUDIO_HTML_TEMPLATE = "audio_template.html"
PLAY_BUTTON = "play_button.html"

# Where data is stored
# BASE_PATH ='/group/project/cstr3/html/sarenne/test_qualtrics/' # where generated experiment datas are stored
# BASE_URL = 'https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/'
BASE_EXT = 'sarenne/qualtrics_pilot10/'
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

    def q_set_up(q_id, export_id):
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
        return new_q

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
        q_text = question_print(q_content)
        q_json['Payload'].update({'QuestionText': q_text})
        return q_json


    # Load the conversation and build speaker turns
    conversation = json.loads(requests.get(BASE_URL + experiment_id + '/conversation.json').text)
    utter_id = int(experiment_id.split("_")[-4])
    speaker_turns = make_speaker_turns(conversation)

    # Store the question set  (NOTE should this be a list?)
    q_set = []
    q_exports = []

    for i, cntxt_id in enumerate(context_ids):

        # import IPython
        # IPython.embed()

        (before, after), indiv = context_conditions[cntxt_id]

        # Generate a discrim turn experiment
        q_export = f'C{cntxt_id}_' + experiment_id
        new_q = q_set_up(q_counter + i + 1, q_export)

        # Fill template with audio choices and text
        new_q = update_choices(new_q, audio_urls, individual=indiv)
        new_q = update_text(new_q, speaker_turns, utter_id, before, after, individual=indiv)
        q_set.append(new_q)
        q_exports.append(q_export)

    return q_set, q_exports

# make n new blocks according to the survey_length
def make_blocks(question_ids, basis_blocks, page_breaks=True, blocks_before=3):
    """
    NOTE this doesn't make new blocks, it just adds questions to the basis_block (elements "Survey Blocks")
    """
    new_blocks = basis_blocks
    # block_elements = []
    block_elements = new_blocks['Payload'][0]['BlockElements'] # Start with the intro and page break in the template
    for i in range(blocks_before, len(question_ids) + blocks_before + 1): # Q1,2 are already loaded from template
    # for q_id in question_ids:
        block_element = OrderedDict()
        block_element['Type'] = 'Question'
        block_element['QuestionID'] = f'QID{i}'
        block_elements.append(block_element)
        if page_breaks:
            block_elements.append({'Type': 'Page Break'})
    new_blocks['Payload'][0]['BlockElements'] = block_elements
    return new_blocks

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
    context_conditions = [((0,0), True), ((0,0), False), ((4,0), True), ((4,0), False), ((2,2), True), ((2,2), False)]
    repeats = 3

    survey_structures = assign_surveys(list(experiment_urls.keys()), list(range(len(context_conditions))), repeats, write=False)

    for survey_id, structure in survey_structures.items():

        # get json to use as basis for new questions
        basis_json = get_basis_json()
        elements = basis_json['SurveyElements']

        # Set the survey ID in all survey_elements
        elements = list(map(set_id, elements))

        # get basic survey components from elements JSON
        basis_blocks = elements[0]
        basis_flow = elements[1]
        rs = elements[2]
        basis_survey_count = elements[7]

        # create list to store generated question blocks
        questions = []
        question_ids = []

        # create counters to use when indexing optional lists
        q_counter = 2 # qualtrics question numbering starts at 1 (and first 'questions' are ethics + the intro)

        for exp_id, context_id in structure.items():

            new_qs, ids = make_discrim_question_set(q_counter=q_counter+1,
                                                    experiment_id=exp_id,
                                                    audio_urls=experiment_urls[exp_id],
                                                    context_conditions=context_conditions,
                                                    context_ids=[context_id,],
                                                    basis_question=elements[-1]
                                                    )
            questions.extend(new_qs)
            question_ids.extend(ids)
            q_counter += len(new_qs)

        # survey_length is determined by number of questions created
        survey_length = q_counter

        # Create all the items in survey elements, with helper function where doing so is not trivial
        blocks = make_blocks(question_ids, basis_blocks)
        flow = basis_flow
        flow['Payload']['Properties']['Count'] = survey_length
        survey_count = basis_survey_count
        survey_count['SecondaryAttribute'] = str(survey_length)
        # add all the created elements together
        elements = [blocks, flow] + elements[2:10] + questions + [rs] # elements[8] is the ethics. elements[9] is intro


        # Add the elements to the full survey
        # Not strictly necessary as we didn't do deep copies of elements
        out_json = basis_json
        out_json['SurveyElements'] = elements

        # Save survey
        print(f'Generated survey {survey_id} with {survey_length} questions')
        with open(SAVE_TEMPLATE + f'_{survey_id}.qsf', 'w+') as outfile:
            json.dump(out_json, outfile, indent=4)

        # Save participant assignments
        with open(SAVE_TEMPLATE + f'_assignments.json', 'w+') as outfile:
            json.dump(survey_structures, outfile)

if __name__ == "__main__":
    main()
