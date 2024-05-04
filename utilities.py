import dateutil.parser

def ConvertStringToDateTime(date_time_str):
    return dateutil.parser.isoparse(date_time_str)