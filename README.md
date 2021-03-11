This is a tool for automating the process of creating online listening tests in Qualtrics.

This README contains information about the forked repo origins (scroll...) as well as some informationt that is specific to `discriminative_turn`-style experiments.

# Discriminative Turns
## End2End Instructions

Currently, the generation process is a bit piecemeal (*cough, modular*) and requires some manual interventions. 

1. Experiments must be generated through the `discriminative_turns` repo, using an `ExperimentGenerator()` object (see `experiment_genertor.ipynb` for examples). Given a dataset and some specifying parameters, this will produce a labelled directory containing target amd negative audio samples (wav files), the index of the target, and the full conversation (JSON file). 


~~2. Data has to be manually moved on nfs ('/group/project/cstr3/html/sarenne/test_qualtrics/‘). Current this is done by `$ scp -r Documents/PhD/discriminative_turns/experiment_samples/sw_40106_148_4_4_2 s1301730@student.ssh.inf.ed.ac.uk:/group/project/cstr3/html/sarenne/test_qualtrics`
   Once it’s there, it can be accessed through the [browser](https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/sw_40106_148_4_4_2/) and Qualtrics!
   NOTE: frustratingly, data can't be hosted on `http://data.cstr.ed.ac.uk/` (which can be accessed through `afs`; this would make moving data slightly easier as AFS is easy to mount while NFS requires ssh access). Instead, data has to be hosted on https://groups.inf.ed.ac.uk (through `nfs`) to be used with Qualtrics. Current best guess as to why is that Qualtrics only reads https urls; the certificate for `https://data.cstr...` is not valid (it points to `groups.inf.ed.ac.uk`). This is known by compute support, not sure when it will be fixed. THIS HAS NOW BEEN FIXED AS COMPUTE SUPPORT UPDATED THE CERTIFICATE~~
   
2. Data has to be manually moved to afs ('afs/inf.ed.ac.uk/group/cstr/sarenne/test_qualtrics/‘) by copying (`cp -r {source/path/} {target/path}`) the files to afs.  
Once it’s there, it can be accessed through the [browser](https://groups.inf.ed.ac.uk/cstr3/sarenne/test_qualtrics/sw_40106_148_4_4_2/) and Qualtrics!

3. To generate experiments automatically through qualtrics, urls to the audio files and conversion.json have to be passed to the `testmaker_discrim_blocks.py` script.
    - To collect a list of urls, run `get_urls()` (currently just IPython, copy-paste from `discriminative_turn_utils.py`) to write a json of {experiment_ids: audio_urls} to your local machine. This file can now be passed as input to generate a qualtrics survey!

4. Update the path of the url JSON file in the `testmaker_discrim_blocks.py` script and run. This will generate a `.qsf` file which can be imported into Qualtrics.

5. (OPTION) For the full experiment, I am adding a question at the beginning and end of all surveys to ensure that all participants are asked atleast 2 gender check questions.  This is being done manually by 
  a) moving all samples + 2 to `datawww`, 
  b) generating the set of ALL urls,
  c) generating a survey from them,
  d) copying 2 questions manually to Qualtrics,
  e) moving those files from datawww and from local dir,
  f) generating the urls again, 
  g) generating the real surveys,
  h) manually adding the 2 questions to each survey (add as a block at the beginning and end, and update the survey flow)

-----------
# Background
This tool reduces number of manual steps required to create a functioning test. It works by generating a JSON file which Qualtrics will interpret to  produce a survey. It was originally created for use in evaluating text-to-speech systems, but has wider applications in speech technology and other audio-related fields.

This is not supported in any way by Qualtrics and is 100% unofficial.

###### Guide contents:
- [Functionality](#functionality)
- [Instructions](#instructions)
  * [Python dependencies](#python-dependencies)
  * [Getting the script](#getting-the-script)
  * [Configuration](#configuration)
    + [`config.py`](#-configpy-)
    + [Default Settings](#default-settings)
      - [For all question types:](#for-all-question-types-)
      - [Transcription questions:](#transcription-questions-)
      - [MUSHRA questions:](#mushra-questions-)
  * [Running the script](#running-the-script)
  * [Importing to Qualtrics](#importing-to-qualtrics)
- [Manual steps](#manual-steps)

# Functionality

It currently supports:
- A/B preference questions (‘Which speech sample sounds more natural?’)
- A/B/C preference questions (as above but with 3 choices)
- Multiple choice questions (‘Does this speech sample contain any errors?’)
- Transcription questions (‘Listen to this audio clip and type what you hear.’)
- MUSHRA style questions (MUltiple Stimuli with Hidden Reference and Anchor)
- MOS test questions (Mean Opinion Score, with 1:5 slider scale)

See a demo test showcasing each question type [here](https://edinburghinformatics.eu.qualtrics.com/jfe/form/SV_0PrKc4KQ7jDXxLn).

<img src="https://raw.githubusercontent.com/evelyndjwilliams/readme-gifs/main/finished-testmaker.gif" width="500" height="370">


<br>A MUSHRA test question created using the testmaker script.

# Instructions

The file `help.md` contains solutions to some issues we encountered while generating surveys.
A Wiki with more comprehensive instructions for setting up listening tests in Qualtrics is [here](https://www.wiki.ed.ac.uk/pages/viewpage.action?spaceKey=CSTR&title=Qualtrics+Listening+Tests)

## Python dependencies

This tool only uses packages from the Python standard library.

## Getting the script

Clone the <Name> GitHub repository with the command:

`git clone https://github.com/jacobjwebber/qualtrics-listening-test-maker.git`

## Configuration

### `config.py`

The script expects the folder `/resources` to contain `.txt` files with lists of your audio URLs.  Some test files are included by default. The necessary file format varies between question types. Requirements for each type are detailed in `config.py`.

Before running the script, the file `config.py` should be updated to contain the correct paths for your URLs, and the correct text for your questions.
(This only applies to the question types included in your test, which you will specify using command line flags. The others won't be executed, so can remain as the default.)


### `combined-template.json`

This file contains the basic building blocks for every available question type. You don't need to modify this file to run the script.

 If you want to extend the script's functionality to include more question types, you should generate a new JSON template file. You can do this by manually creating a survey in Qualtrics which meets your requirements, and exporting the survey file (Tools --> Export).


### Number of questions
The number of questions in the survey is taken automatically from the number of filenames in your lists.

### Default Settings
Default question settings are determined by the template file `combined-template.JSON`. These settings include:

#### For all question types
- Answer choices are presented in random order (except for multiple choice questions).
- Force response, so all questions must be answered before proceeding.

#### Transcription questions
- Audio playback is disabled for transcription tests (so each audio clip can be played only once).

#### MUSHRA questions
- The default HTML5 audio player is replaced by a simple play/pause button, as the hidden reference could be identified by its duration.
- At least one sample must be rated == 100 (in line with the guidelines set out in ITU-R BS.1534-1).

Changing these settings requires either editing the template file (`combined-template.JSON`) or creating a new template by creating a question in Qualtrics with the correct specifications and exporting the survey file.


## Running the script

The script is run from the command line, using flags to specify the desired question types.

Flags:
- `-ab` = A/B preference
- `-abc` = A/B/C preference
- `-mc` = multiple choice
- `-trs` = audio transcription
- `-mushra` = MUSHRA
- `mos` = MOS

Questions will be added to the output test in the order you supply the flags.

E.g. to create a test with MUSHRA then audio transcription questions, use the command:

`python testmaker.py -mushra -trs`

<img src="https://raw.githubusercontent.com/evelyndjwilliams/readme-gifs/main/run-testmaker.gif" width="420" height="200">

<br>


Running the script will create a .qsf (Qualtrics Survey Format) file called `output-survey.qsf`.

## Importing to Qualtrics
This file can be imported to Qualtrics (following the steps [here](https://www.qualtrics.com/support/survey-platform/survey-module/survey-tools/import-and-export-surveys/)) and will be converted to a working listening test.

<img src="https://raw.githubusercontent.com/evelyndjwilliams/readme-gifs/main/import-testmaker.gif" width="420" height="330">



# Manual steps

While this script generates test questions, other elements of the test still have to be configured manually in Qualtrics. These include consent forms and instructions, as well as specific flow settings, like randomly assigning participants to groups.
