

[ANS]
import datetime

def parse_expenses(expenses_string):
    """Parse the list of expenses and return the list of triples (date, value, currency).
    Ignore lines starting with #.
    Parse the date using datetime.
    Example expenses_string:
        2016-01-02 -34.01 USD
        2016-01-03 2.59 DKK
        2016-01-03 - 2.72 EUR
    """
    result = []
    for line in expenses_string.split('\n'):
        if not line or line[0] == '#':
            continue
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        date, value, currency = parts[:3]
        try:
            result.append((datetime.date(*map(int, date.split('-'))), float(value), currency))
        except ValueError as e:
            print("Invalid date format")
    return result
[/ANS]
