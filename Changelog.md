#### tomato v0.8.1
 - Input and output filepaths are forced to UTF-8
 - Plotter._plot_stable_pitches skips uncalculated stable pitches
 - Carried get_lilypond_bin_path from scoreconverter to bin_caller

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
 - Makam ,tonic, transposition and tempo information is annotated in 
 ```Plotter.plot_audio_features``` 
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
