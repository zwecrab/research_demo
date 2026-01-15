@echo off
:: This script activates the Python virtual environment for the ESG project.
::
:: 🛑 IMPORTANT: You must run this from your terminal using the 'call' command.
::
::    Example:   call activate_esg.bat
::

echo [INFO] Activating Python environment at D:\DSAI\ESG\env...
call "D:\DSAI\ESG\env\Scripts\activate.bat"

echo [SUCCESS] Environment is now active.