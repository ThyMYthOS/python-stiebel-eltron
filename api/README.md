# API definition

This folder contains the csv files which are describing the registers of the ISG modbus interface. The values in the cvs files are manually copied from the [Stiebel Eltron modbus documentation](https://www.stiebel-eltron.ch/content/dam/ste/ch/de/downloads/kundenservice/smart-home/Modbus/Modbus%20Bedienungsanleitung.pdf).
The files can either be manually edited with your Code Editor (e.g. Visual Studio Code)  or edited with a spreadsheet editor like LibreOffice or Excel. The encoding of the files is UTF-8.

A row may deliberately depart from the documentation where a device contradicts it. The Comments column says so next to that row and keeps the documented value visible, so the transcription and the correction can both be checked.

The addresses here follow the documentation's one-based numbering. `scripts/generate.py` subtracts one from each of them for the zero-based PDU addresses the generated modules use. `mbpoll` is also one-based unless it is given `-0`, which switches it to zero-based PDU addressing, so it is worth establishing which convention a reported register number is in before comparing it against a row here.

