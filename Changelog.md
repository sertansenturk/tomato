#### tomato v0.13.0
 - Refactored metadata package: [Pull request #84](https://github.com/sertansenturk/tomato/pull/84)

#### tomato v0.12.2
- Solved the pool error occurring in Essentia version 2.1-beta5-dev: [Pull request #86](https://github.com/sertansenturk/tomato/pull/#88) (by [Miguel García Casado](https://github.com/miguelgcasado))

#### tomato v0.12.1
- Added missing makam & tonic estimation model: [Pull request #86](https://github.com/sertansenturk/tomato/pull/#86)

#### tomato v0.12.0
 - Made the package Python 3 compatible: [Pull request #78](https://github.com/sertansenturk/tomato/pull/78)

#### tomato v0.11.0
 - Ported all makam analysis libraries into tomato: [Pull request #77](https://github.com/sertansenturk/tomato/pull/77)

#### tomato v0.10.1
 - Updated SymbTr-extras to the latest version (v0.4.0)
 - Corrected a bug when ```flags``` input is not passed to ```ScoreConversion.mu2_to_musicxml```

#### tomato v0.10.0
 - Integrated mu2 to MusicXML conversion (courtesy of Mogens Lundholm)
 - Updated seyiranalyzer to the latest version (v1.2.0)
 - Updated predominantmelodymakam to the latest version (v1.2.1)

#### tomato v0.9.1
 - Added DOI
 - Added Contributors
 - Moved package version to tomato init file
 - Minor changes in setup to fetch the version automatically from ```tomato.__version__```

#### tomato v0.9.0
 - Integrated makam recognition
 - Added training models precomputed from [otmm_makam_recognition_dataset](https://github.com/MTG/otmm_makam_recognition_dataset/tree/dlfm2016) for tonic identification and makam recognition
 - Fizes a bug where method parameters setters of _pitch distribution_ and _makam recognizer_ (stored in tow dictionaries) are failed to be set
 - Incremented the version of morty in requirements

#### tomato v0.8.1
 - Input and output filepaths are forced to UTF-8
 - Plotter._plot_stable_pitches skips uncalculated stable pitches
 - Carried get_lilypond_bin_path from scoreconverter to bin_caller
 - Added licence info to the README

#### tomato v0.8.0
 - Updated required packages to the latest releases
 - Set system-wide installed LilyPond to default Linux configuration
 - Added support for eyed3>=0.7.5
 - Partial caller now handles MATLAB runtime errors
 - Change on svg regex to match only notes
 - Added stacklevel to the warnings
 - The language is forced to en_US.utf8 in bincaller

#### tomato v0.7.1
 - Changed the mappings in the svg files from ly to SymbTr-txt indices
 - Refactored module and object names according to PEP8 conventions
 - Fixed the broken imports from refactored packages

#### tomato v0.7.0
 - Added CompleteAnalyzer class
 - Refactored ParamSetter class to the abstract Analyzer class. It is
 inherited by all "Analyzer" classes.
 - Improved partial processing when calling the main "analyze" method of
 each analysis class.
 - "analyze" methods now have a (variable length) **kwargs input as the
 input features. These features are not computed and used in the subsequent
 analysis steps.
 - Added ```ScoreConverter``` class
 - Added input parsing to ```Plotter.plot_audio_features```
 - Makam ,tonic, transposition and tempo information is annotated in ```Plotter.plot_audio_features``` 
 - Improved code quality
 - All note indices in the outputs are fixed to **1-indexing** according to
 the Symbtr-txt convention (not the pythonic 0-indexing).
 - Updated requirements
 - Improved verbosity and warnings
 - Execution time of each step is printed if the verbose is True.

#### tomato v0.6.0
 - Added audio metadata fetching from MusicBrainz using [makammusicbrainz](https://github.com/sertansenturk/makammusicbrainz/releases/tag/v1.2.0).
 - Makam can be now obtained from the fetched audio metadata 
 - Updated the versions of [ahenkidentifier](https://github.com/sertansenturk/ahenkidentifier/releases/tag/v1.4.0) and [symbtrdataextractor](https://github.com/sertansenturk/symbtrdataextractor/releases/tag/v2.0.0-alpha.3)

#### tomato v0.5.0
 - Analysis can be run with partial success when some inputs are not available or some methods fails (Issue [#24](https://github.com/sertansenturk/tomato/issues/24))

#### tomato v0.4.0
 - Created IO, Plotter and ParamSetter classes
 - Refactored the code to use the methods from above classes for shared processes
 - All output variables are now in snake_case
 - Better saving and loading
 - Improved code quality

#### tomato v0.3.0
 - Added joint audio-score analysis
 - Minor improvement and bug fixes in SymbTrAnalyzer and AudioAnalyzer classes

#### tomato v0.2.0
 - Added SymbTr-score analysis
 - Simplified and improved the installation process

#### tomato v0.1.0
 - Added audio analysis
