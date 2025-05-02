# Tools Directory

This directory contains the tools available to the Agent Shop Talk platform.

## Adding a New Tool

1.  Create a new directory for your tool (e.g., `tools/my_new_tool/`).
2.  Use the `tools/tool_template/` as a starting point.
3.  Implement your tool logic in `tool.py`.
4.  Fill out the `metadata.json` file with the tool's name, description, and parameters.
5.  Update the `__init__.py` if necessary for registration (details TBD).

## Removing a Tool

1.  Delete the tool's directory (e.g., `rm -rf tools/my_tool/`).
2.  The system should automatically detect the removal (details TBD). 