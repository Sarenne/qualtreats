import glob
import json
import random
import re

""""""

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


def context_print(utter_id, speaker_turns, turns_before, turns_after, individual=False):
    """Print the speaker turns before and after the target utterance (utter1)"""

    # Find the target utter as a target turn
    target_turn = [turn for turn in speaker_turns if utter_id in turn['utter_id']][0]
    target_turn_id = target_turn['turn_id']

        # Print bubble turns
    def bubbles_print(txt_list, last=True, bold=False):

        start = stop = ''
        if bold:
            start, stop = '<b>', "</b>"

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
        Print each utterance in the speaker turn. Special behaviour for utter1 turn: only display utter1
        unless context AFTER is >0, then display all potential utterances in the turn (utter1_all).
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


    # # Print turns
    # def print_turn(turn, utter1_all, individual):
    #     """
    #     Print each utterance in the speaker turn. Special behaviour for utter1 turn: only display utter1
    #     unless context AFTER is >0, then display all potential utterances in the turn (utter1_all).
    #     """
    #     turn_str = ""
    #     speaker = turn["speaker"][0]
    #
    #     # BOLD utter0 (full turn)
    #     if utter_id - 1 in turn["utter_id"]:
    #         for text in turn["text"]:
    #             if individual:
    #                 turn_str += f'{side_starts[speaker]} {print_transcript(text)} {end}'
    #             else:
    #                 turn_str += f'{side_starts[speaker]} <b>{print_transcript(text)}</b> {end}'
    #     # BOLD utter1
    #     elif utter_id in turn["utter_id"]:
    #         turn_str += f'{side_starts[speaker]} <b>{print_transcript(turn["text"][0])}</b> {end}'
    #         if utter1_all and len(turn['text']):
    #             for text in turn["text"][1:]:
    #                 turn_str += f'{side_starts[speaker]} {print_transcript(text)} {end}'
    #     # normal other utters (full turns)
    #     else:
    #         for text in turn["text"]:
    #             turn_str += f'{side_starts[speaker]} {print_transcript(text)} {end}'
    #
    #     return turn_str
    #
    # # Formatting
    # def markdown_start(align, color, font_size=12, width=500):
    #     """Return the markdown start symbol for a particular speaker (alignment, color)"""
    #     return f'<div style="text-align: {align}; width:{width}px"> <span style="color:{color}; font-size: {font_size}pt">'
    #
    # side_starts = {"A": markdown_start('right', '#065B9A'), #'<div style="text-align: right"> <span style="color:#065B9A; font-size: 18pt">',
    #                "B": markdown_start('left', '#069A62'),}
    # end = "</span> </div>"


    turn_start = {"A":' <div class="yours messages">',
                  "B": '<div class="mine messages">',
                 }
    turn_end = "</div>"

    # The actual printing...
    full_string = '<div class="chat">'
    for turn in speaker_turns[max(0, target_turn_id - turns_before - 1 ):
                               min(target_turn_id + turns_after + 1, len(speaker_turns))]:

        turn_string = turn_start[turn['speaker'][0]]

        turn_string += print_turn_css(turn, turns_after>0, individual)
        turn_string += turn_end
        full_string += turn_string
# #     return tt
#
#     # The actual printing...
#     full_string = ""
#     for turn in speaker_turns[max(0, target_turn_id - turns_before - 1 ):
#                                min(target_turn_id + turns_after + 1, len(speaker_turns))]:
#         full_string += print_turn(turn, turns_after>0, individual)

    full_string += turn_end
    return full_string

def get_urls(experiment_ids=[], write=False,
             base_nfs_path='/group/project/cstr3/html/sarenne/test_qualtrics/',
             base_path='/afs/inf.ed.ac.uk/group/cstr/datawww/sarenne/test_qualtrics/',
             base_cstr_url='https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/',
             base_url='https://data.cstr.ed.ac.uk/sarenne/test_qualtrics/'):
    """
    Return the urls for files stored in https://groups.inf.ed.ac.uk/cstr3/ by checking nfs

    NOTE access to nfs requires working through SSH! Therefore, use scp to copy back to local machine.
    """
    # output_path = '/afs/inf.ed.ac.uk/user/s13/s1301730/Documents/discriminitive_turns/qualtrics_resources'
    output_path = 'discrim_turn_resources/'
    # http://data.cstr.ed.ac.uk/sarenne/test_qualtrics/
    # https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/sw_40106_148_4_4_2/
    if len(experiment_ids) < 1:
        experiment_ids = [p.split('/')[-1] for p in glob.glob(base_path + '/*')]

    experiment_data = {exp_id: glob.glob(base_path + exp_id + '/*.wav') for exp_id in experiment_ids}
    url_data = {exp_id: [base_url + exp_id + '/' + e.split('/')[-1] for e in files] for exp_id, files in experiment_data.items()}
    if write:
        with open(output_path + 'urls.json', 'w+') as fs:
            json.dump(url_data, fs)

    return experiment_data, url_data
