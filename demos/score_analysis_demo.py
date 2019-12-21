#!/usr/bin/env python
# coding: utf-8

# In[1]:


from tomato.symbolic.symbtranalyzer import SymbTrAnalyzer
import os


# In[2]:


# symbtr name, 
# it is needed if the filename is modified from the SymbTr naming convention
symbtr_name = 'ussak--sazsemaisi--aksaksemai----neyzen_aziz_dede'

# score filepaths
txt_filename = os.path.join(symbtr_name, symbtr_name + '.txt')
mu2_filename = os.path.join(symbtr_name, symbtr_name + '.mu2')

# instantiate analyzer object
scoreAnalyzer = SymbTrAnalyzer(verbose=True)


# You can use the single line call "analyze," which does all the available analysis simultaneously

# In[3]:


score_data = scoreAnalyzer.analyze(txt_filename, None, symbtr_name=symbtr_name)


# In[4]:



# ... or you can call all the methods individually
# 

# In[5]:


from tomato.metadata.symbtr import SymbTr as SymbTrMetadata
from tomato.symbolic.symbtr.reader.txt import TxtReader
from tomato.symbolic.symbtr.reader.mu2 import Mu2Reader
from tomato.symbolic.symbtr.dataextractor import DataExtractor
from tomato.symbolic.symbtr.section import SectionExtractor
from tomato.symbolic.symbtr.segment import SegmentExtractor
from tomato.symbolic.symbtr.rhythmicfeature import RhythmicFeatureExtractor

# relevant recording or work mbid, if you want additional information from musicbrainz
# Note 1: MBID input will make the function returns significantly slower because we
#         have to wait a couple of seconds before each subsequent query from MusicBrainz.
# Note 2: very rare but there can be more that one mbid returned. We are going to use 
#         the first work to get fetch the metadata
mbid = SymbTrMetadata.get_mbids_from_symbtr_name(symbtr_name)[0]

# read the txt score
txt_score, is_score_content_valid = TxtReader.read(
    txt_filename, symbtr_name=symbtr_name)

# read metadata from musicbrainz
mb_metadata, is_mb_metadata_valid = SymbTrMetadata.from_musicbrainz(
    symbtr_name, mbid=score_data['mbid'])

# add duration & number of notes
mb_metadata['duration'] = {
    'value': sum(score_data['score']['duration']) * 0.001, 'unit': 'second'}
mb_metadata['number_of_notes'] = len(txt_score['duration'])

# read metadata from the mu2 header
mu2_header, header_row, is_mu2_header_valid = Mu2Reader.read_header(
    mu2_filename, symbtr_name=symbtr_name)

# merge metadata
score_metadata = DataExtractor.merge(mb_metadata, mu2_header)

# sections
section_extractor = SectionExtractor()
sections, is_section_data_valid = section_extractor.from_txt_score(
    txt_score, symbtr_name)

# annotated phrases
segment_extractor = SegmentExtractor()
phrase_annotations = segment_extractor.extract_phrases(
    txt_score, sections=sections)

# Automatic phrase segmentation on the SymbTr-txt score using pre-trained model
segment_bounds = scoreAnalyzer.segment_phrase(txt_filename, symbtr_name=symbtr_name)
segments = segment_extractor.extract_segments(
    txt_score,
    segment_bounds['boundary_note_idx'],
    sections=sections)

# rhythmic structure
rhythmic_structure = RhythmicFeatureExtractor.extract_rhythmic_structure(
    txt_score)
