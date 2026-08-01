[app]
# (str) Title of your application
title = EWT360刷时长工具

# (str) Package name
package.name = ewt360

# (str) Package domain (needed for android/ios packaging)
package.domain = com.johnstudio

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty by default)
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty by default)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty by default)
source.exclude_dirs = tests, bin, build

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 5.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# Dependencies for EWT360 - requests + kivy
requirements = python3,kivy==2.3.0,requests==2.31.0

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OSX Specific
#

#
# author = © Copyright Info

# (str) Name of the author
# author = John Studio

# (str) License
# license = MIT

# (list) A list of licenses to include in the app
#license_files = license.txt

# (str) The path to the folder where the app's data is stored
# app_data_dir = /sdcard/.ewt360

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
android.presplash_color = #10131a

# (string) Presplash animation (for new android toolchain)
# Valid options: ['zoom_in', 'zoom_out', 'fade_in', 'fade_out', 'bounce', 'slide_in']
# android.presplash_anim = zoom_in

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 34

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then skip trying to update the Android SDK
# This can be useful to prevent unnecessary network calls
android.skip_update = False

# (bool) If True, then automatically accept SDK license agreements
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (list) Pattern to whitelist for the whole project
#android.whitelist =

# (str) Path to a custom whitelist file
#android.whitelist_src =

# (str) Path to a custom blacklist file
#android.blacklist_src =

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching, for example:
# OUYA-ODK/libs/*.jar
#android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# (list) List of Java files to add to the android project (can be java or a
# directory containing the files)
#android.add_src =

# (list) Android AAR archives to add (currently works only with sdl2_gradle
# bootstrap)
#android.add_aars =

# (list) Gradle dependencies to add (currently works only with sdl2_gradle
# bootstrap)
#android.gradle_dependencies =

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package, or any package from AndroidX library
android.enable_androidx = True

# (list) Add Java compile options
#android.add_compile_options = -Xlint:deprecation,-Xlint:unchecked

# (list) Gradle repositories to add {can be necessary for some android.gradle_dependencies}
#android.add_gradle_repositories =

# (list) Packages to add to the 'requirements' key in 'build.gradle'
#android.add_build_requirements =

# (list) Java classes to add to the 'main' activity (can be string or list)
#android.add_activity = com.example.ExampleActivity

# (str) OUYA Console category. Should be one of GAME or APP
# If you leave this blank, OUYA support will not be enabled
#android.ouya.category = GAME

# (str) Filename of OUYA Console icon. It must be a 732x412 PNG image.
#android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) XML file to include as an intent filters in <activity> tag
#android.manifest.intent_filters =

# (str) launchMode to set for the main activity
#android.manifest.launch_mode = standard

# (list) Android additional intent attributes for the main activity
#android.manifest.activity_attributes =

# (list) Android extra custom tags to add in the manifest
#android.manifest.extra_tags =

# (bool) Run the build in debug mode
android.debug = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (int) Amount of memory in MB for the JVM
#android.jvm_mem = 2048

# (bool) Enable or disable the usage of the newest AndroidX features
# android.use_androidx = True

# (str) Bootstrap to use for android builds
#android.bootstrap = sdl2

# (int) Max API for new android toolchain
#android.maxapi = 34

# (str) Space-separated list of locales to pack in the APK
#android.locales = en_US

# (bool) Enable or disable the build status bar
#android.build_status_bar = True

# (str) Path to the python-for-android distribution directory
#android.p4a_dir =

# (str) Path to the buildozer directory
#buildozer.dir =

# (str) Path to the buildozer.spec file
#buildozer.spec = %(source.dir)s/buildozer.spec

# (bool) Set to True to use the old android toolchain (deprecated)
#android.old_toolchain = False

# (str) Custom Python distribution name
#android.python_dist_name = myapp

# (str) Custom Python distribution version
#android.python_dist_version = 3.10.10

# (list) A list of Python modules to exclude from the build
#android.exclude_modules =

# (list) A list of Python modules to include in the build
#android.include_modules =

# (str) The name of the Python file to use as the entry point
# android.entrypoint is already set above to org.kivy.android.PythonActivity
# The Python entry file is main.py (set via buildozer's default behavior)
# python.entrypoint = main.py

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug, 3 = verbose)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output storage, absolute or relative to spec file
# output_dir = ./bin

# (str) Path to the buildozer cache directory
# cache_dir = ./.buildozer/cache

# (list) List of buildozer hooks
# buildozer.hooks =

# (str) Default command to run when none is provided
# default_command = debug

# (str) Default profile to use when none is specified
# default_profile = debug

# (bool) Whether to use the buildozer UI
# use_ui = False

# (bool) Whether to use the buildozer web UI
# use_web_ui = False

# (str) The default text editor to use
# editor = vim

# (bool) Whether to use colored output
# colored_output = True

# (bool) Whether to use unicode characters in output
# unicode_output = True

# (bool) Whether to use the buildozer logo
# show_logo = True

# (bool) Whether to check for buildozer updates
# check_for_updates = True

# (bool) Whether to automatically update buildozer
# auto_update = False

# (str) The URL to check for updates
# update_url = https://buildozer.readthedocs.io/en/latest/

# (str) The URL to download updates from
# download_url = https://github.com/kivy/buildozer/archive/master.zip

# (str) The command to run after a successful build
# post_build_hook =

# (str) The command to run before a build
# pre_build_hook =
