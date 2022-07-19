# ppdm-report
Extract Job information from Dell PowerProtect Data Manager REST API and create a report in Teams channel
## Functionality clarification
The generated Teams card includes:
- a summary of the backup activity in the last 24 hours
- a button with a link pointing to PPDM's GUI
- another button with a link download the detailed report from an S3 bucket

## Acknowledgements
The code uses a pre-compiled Python tool for Windows that generates a detailed backup report on Excel format. You can find the EXE and the Python code in [Raghava Jainoje's repo](https://github.com/rjainoje). Kudos to Raghava!

## Permissions
This code makes use of the "/activities" endpoint. According to the PowerProtect Data Manager documentation the "/activities" endpoint supports execution by the following roles: Administrator, User, Backup Administrator, Restore Administrator. You can get more details about this and other Dell Technologies REST APi's at the [Dell Developer Portal](https://developer.dell.com/apis/4378/versions/19.11)


## Compatibility
Code has been tested with Python 3.9.2

Library dependencies are available in 'requirements.txt'
## Disclaimer
Barely no error checking has been implemented. Feel free to download it and harden it if you want to use in production. Use at your own risk
