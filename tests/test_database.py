import pytest
from database import get_provisions
import logging

def test_get_provisions_integ():
    """
    Tests the addition of two numbers.
    """
    res = get_provisions(limit = 5)
    logging.info('-------starting')
    for p in res:
        print('-----')
        logging.info(f'{p.id} = {p.description}')
        
    assert len(res) == 5