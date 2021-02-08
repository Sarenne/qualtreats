import glob
import json
import random
import re
import string

import numpy as np

"""This file contains helper methods for making surveys in Qualtrics"""

question_intro = '<div>Consider the following segment of a phone conversation (you will hear the sections in <u><b>underlined bold</b></u>):</div>'
question_outro = '<div><u>Only one of the following segments is the <b>true</b> turn-response in this conversation. Assign each audio segment a score of how likely it is to be the <b>true</b> turn-response in this conversation</u></div>'

def print_transcript(text):
    """
    Clean transcript for printing in the experiment player:
    - unintelligible speech: keep
    - speech events (eg. {laugh}, [distortion]): keep
    - punctuation (eg \, \. \- _should this include '?'_): keep
    """
    # remove filler speech, and capitalisation symbols
    clean = re.sub(r'[%^~]', '', text)
#     # remove unintelligible speech
#     clean = re.sub(r'\(.*\)', '', clean)
#     # remove speech acts
#     clean = re.sub(r"[\{\[].*?[\}\]]", "", clean)
#     # remove punctuation
#     clean = re.sub(r"[\,\.\?]", "", clean)
    # remove trailing and multiple spaces
    clean = re.sub(' +', ' ', clean).strip()
    return clean

def make_speaker_turns(conversation):
    """
    Split conversation into speaker turns (group utterances by speaker) and return a turn object (very similar to an
    utter object)

    E.g.,
        {'conv_id': ['sw_40016'],
         'utter_id': [92],
         'start': [152.57],
         'stop': [154.06],
         'speaker': ['A'],
         'text': ['{breath}  %oh, okay'],
         'clean_text': ['%oh okay'],
         'turn_id': 55
         }
    """

    # # Load conversation (list of utterance dict objs)
    # with open(experiment_path + '/conversation.json') as json_file:
    #     c = json.load(json_file)
    c = conversation

    # Split conversation into speaker turns (list of utterances grouped by speaker)
    speaker_list = []
    speaker = c[0]['speaker']
    cont = []
    for utter in c:
        if speaker == utter['speaker']:
            cont.append(utter)
        else:
            speaker_list.append(cont)
            cont = [utter]
            speaker = utter['speaker']
    speaker_list.append(cont)

    # Convert list of turns into single turn object
    speaker_turns = []
    for i, elem in enumerate(speaker_list):
        turn = {k: [d[k] for d in elem] for k in elem[0]}
        turn['turn_id'] = i
        speaker_turns.append(turn)

    return speaker_turns


def question_print(question_content, before_text=question_intro, after_text=question_outro):
    """Print the full question text for Qualtrics, including intro + instructions"""
    return before_text + question_content + after_text


def context_print(utter_id, speaker_turns, turns_before, turns_after, individual=False):
    """Print the speaker turns before and after the target utterance (utter1)"""

    # Find the target utter as a target turn
    target_turn = [turn for turn in speaker_turns if utter_id in turn['utter_id']][0]
    target_turn_id = target_turn['turn_id']

    # Print chat bubble turns
    def bubbles_print(txt_list, last=True, bold=False):
        """
        Generic method for returning list of turn content as chat bubbles. Note that this doesn't return the full chat
        turn. Bubbles can be either class {message, message last (with a message tail)}

        Options for returning 'message last' style message and bold text.
        """

        start = stop = ''
        if bold:
            start, stop = '<u><b>', "</b></u>"

        last = ' last'
        if not(last):
            last = ''

        full_text = ''
        for t in txt_list[:-1]:
            full_text += f'<div class="message">{start}{print_transcript(t)}{stop}</div>'
        full_text += f'<div class="message{last}">{start}{print_transcript(txt_list[-1])}{stop}</div>'

        return full_text

    def print_turn_css(turn, utter1_all, individual):
        """
        Print each utterance in the speaker turn. Special behaviour for
        - utter1: utter1 is always in bold. Only display speaker turns after utter1 if context AFTER is >0 (utter1_all)
        - utter0: all turns can be bold (i.e., if they are in the audio) or not
        - (all others): print all speaker turns in non-bold
        """
        turn_text = ''
        speaker = turn["speaker"][0]

        # BOLD utter0 (full turn)
        if utter_id - 1 in turn["utter_id"]:
            if individual:
                turn_text += bubbles_print(turn["text"], bold=False)
            else:
                turn_text += bubbles_print(turn["text"], bold=True)
        # BOLD utter1
        elif utter_id in turn["utter_id"]:

            if utter1_all:
                turn_text += bubbles_print([turn["text"][0]], bold=True, last=len(turn['text'])>1)
                if len(turn['text']) > 1:
                    turn_text += bubbles_print(turn["text"][1:], bold=False)
            else:
                turn_text += bubbles_print([turn["text"][0]], bold=True)

        # normal other utters (full turns)
        else:
            turn_text += bubbles_print(turn["text"], bold=False)

        return turn_text

    turn_start = {"A":' <div class="yours messages">',
                  "B": '<div class="mine messages">',
                 }
    turn_end = "</div>"
    turn_dots = '<div class="dots messages"><div class="message"> .  .  . </div></div>'

    # The actual printing...
    full_string = '<div class="chat">' + turn_dots
    for turn in speaker_turns[max(0, target_turn_id - turns_before - 1 ):
                               min(target_turn_id + turns_after + 1, len(speaker_turns))]:
        turn_string = turn_start[turn['speaker'][0]]
        turn_string += print_turn_css(turn, turns_after>0, individual)
        turn_string += turn_end

        full_string += turn_string

    full_string += turn_dots + turn_end

    return full_string



"""
Methods for qualtrics survey set up. Surveys require pointers to audio files (urls), and description of survey structure
to generate (experiment_ids, and context conditions to use)
"""

OUTPUT_PATH = 'discrim_turn_resources/'
# output_path = '/afs/inf.ed.ac.uk/user/s13/s1301730/Documents/discriminitive_turns/qualtrics_resources'
# http://data.cstr.ed.ac.uk/sarenne/test_qualtrics/
# https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/sw_40106_148_4_4_2/

def get_urls(experiment_ids=[], write=False,
             base_nfs_path='/group/project/cstr3/html/sarenne/test_qualtrics/',
             path_ext = 'qualtrics_pilot10/',
             base_path='/afs/inf.ed.ac.uk/group/cstr/datawww/sarenne/',
             base_cstr_url='https://groups.inf.ed.ac.uk/cstr3/sarenne/',
             base_url='https://data.cstr.ed.ac.uk/sarenne/'):
    """
    Return the urls for files stored in https://groups.inf.ed.ac.uk/cstr3/ by checking nfs

    NOTE access to nfs requires working through SSH! Therefore, use scp to copy back to local machine.
    """

    if len(experiment_ids) < 1:
        experiment_ids = [p.split('/')[-1] for p in glob.glob(base_path + path_ext + '/*')]

    experiment_data = {exp_id: glob.glob(base_path + path_ext + exp_id + '/*.wav') for exp_id in experiment_ids}
    url_data = {exp_id: [base_url + path_ext + exp_id + '/' + e.split('/')[-1] for e in files] for exp_id, files in experiment_data.items()}
    if write:
        with open(OUTPUT_PATH + 'urls.json', 'w+') as fs:
            json.dump(url_data, fs)

    return experiment_data, url_data


def assign_surveys(experiment_ids, context_conditions, repeats, write=False):
    """
    For a set of experiment ids, write a json file to structure a set of surveys st for each experiment_id,
    each context condition is included in 'repeats' surveys, and each survey only contains 1 instance of a
    particular experiment_id.

    Return:
        json dict of {survey_id: {experiment_id: context_condition,
                                  ...
                                  },
                                  ...
                     }

    """

    def assign_participant(part_key, assignments):
        """
        Each participant will be assigned exactly (or at most?) 1 context condition per sample

        Args
            part_key (str): participant key (letter)
            assignments (list of arrays): list of arrays corresponding to the grouping per context condition
        """
        return [context_conditions[i] for i, group in enumerate(assignments) if part_key in group][0]

    def assign_sample(sample_id):
        """"
        For each sample, split participants randomly and evenly between the context conditions st each participants is only assigned to a single context condition. Update each participant's assigned context condition in participation dict.

        Args
            contexts (list of tuples): list of context conditions to assign for each experiment id
            repeats (int): number of times each context condition should be assigned
            sample_id (str): experiment id that is being assigned
            participants (dict of dicts): dict that contains the assignments for each participant

        Return
            Updated version of the participant dict (with new assignments for the particular sample)
        """
        part_keys = list(participants.keys())
        np.random.shuffle(part_keys)
        assigns = np.array_split(part_keys, len(context_conditions))

        for p in participants:
            participants[p][sample_id] = assign_participant(p, assigns)

        return participants

    # the main loop
    parts = list(string.ascii_lowercase)[:len(context_conditions * repeats)]
    participants = {p:{} for p in parts}

    for exp in experiment_ids:
        participants = assign_sample(exp)

    if write:
        with open(OUTPUT_PATH + 'randomized_structure.json', 'w+') as fs:
            json.dump(participants, fs)

    return participants
