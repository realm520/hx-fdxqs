# encoding=utf8

import datetime
import logging


# 1-minute K-Line is the base of all other cycles
# the gap more than 1 minute will be filled with previous k_close data.
class KLine1MinObj():
    def __init__(self, k_obj):
        logging.debug("KLine1MinObj created")
        self.k_objs = []
        self.current_k_obj_idx = -1
        if k_obj is not None:
            self.k_objs.append({
                'k_open': k_obj.k_open,
                'k_close': k_obj.k_close,
                'k_low': k_obj.k_low,
                'k_high': k_obj.k_high,
                'base_amount': k_obj.base_amount,
                'quote_amount': k_obj.quote_amount,
                'block_num': k_obj.block_num,
                'start_time': k_obj.timestamp})
            self.current_k_obj_idx = 0


    def get_start_time(self, start_time):
        return start_time.replace(second=0, microsecond=0)

    def process_tick(self, tick):
        logging.debug("Process tick: [%d, %d, %s]" % (tick.block_num, tick.base_amount, tick.timestamp))
        price = float(tick.quote_amount) / float(tick.base_amount)
        if self.current_k_obj_idx == -1:
            logging.debug("Init data of k line")
            self.k_objs.append({
                'k_open': price,
                'k_close': price,
                'k_low': price,
                'k_high': price,
                'base_amount': tick.base_amount,
                'quote_amount': tick.quote_amount,
                'block_num': tick.block_num,
                'start_time': self.get_start_time(tick.timestamp)})
            self.current_k_obj_idx = 0
        else:
            while True:
                start_time = self.k_objs[self.current_k_obj_idx]['start_time']
                next_time = start_time + datetime.timedelta(minutes=1)
                time_diff = tick.timestamp - start_time
                if time_diff.total_seconds() < 0: # invalid tick in the past
                    logging.warn("Tick in the past: %s - %s" % (str(tick.timestamp), str(start_time)))
                    return
                elif start_time.minute != tick.timestamp.minute and time_diff.total_seconds() > 0:
                    logging.info("Fill the gap between [%s] and [%s]" % (start_time, tick.timestamp))
                    self.k_objs.append({
                        'k_open': self.k_objs[self.current_k_obj_idx]['k_close'],
                        'k_close': self.k_objs[self.current_k_obj_idx]['k_close'],
                        'k_low': self.k_objs[self.current_k_obj_idx]['k_close'],
                        'k_high': self.k_objs[self.current_k_obj_idx]['k_close'],
                        'base_amount': 0,
                        'quote_amount': 0,
                        'block_num': tick.block_num,
                        'start_time': next_time
                    })
                    self.current_k_obj_idx += 1
                else:
                    logging.debug("Update k line record: %s" % tick.timestamp)
                    self.k_objs[self.current_k_obj_idx]['k_close'] = price
                    if self.k_objs[self.current_k_obj_idx]['k_low'] > price:
                        self.k_objs[self.current_k_obj_idx]['k_low'] = price
                    if self.k_objs[self.current_k_obj_idx]['k_high'] < price:
                        self.k_objs[self.current_k_obj_idx]['k_high'] = price
                    self.k_objs[self.current_k_obj_idx]['base_amount'] += tick.base_amount
                    self.k_objs[self.current_k_obj_idx]['quote_amount'] += tick.quote_amount
                    break

    def get_k_data(self):
        return self.k_objs


# All the cycles except 1-minute will based on 1-mite k-data
class KLine5MinObj(KLine1MinObj):
    def __init__(self, k_obj):
        logging.debug("KLine5MinObj created")
        KLine1MinObj.__init__(self, k_obj) 
        self.cycle_of_base = 5


    def get_start_time(self, start_time):
        minute = start_time.minute - start_time.minute % self.cycle_of_base
        return start_time.replace(minute=minute, second=0, microsecond=0)


    def get_time_delta(self):
        return datetime.timedelta(minutes=self.cycle_of_base)


    def process_tick(self, tick):
        logging.debug("Process tick: [%d, %d, %s]" % (tick.block_num, tick.base_amount, tick.timestamp))
        if self.current_k_obj_idx == -1:
            logging.debug("Init data of k line")
            
            self.k_objs.append({
                'k_open': tick.k_open,
                'k_close': tick.k_close,
                'k_low': tick.k_low,
                'k_high': tick.k_high,
                'base_amount': tick.base_amount,
                'quote_amount': tick.quote_amount,
                'block_num': tick.block_num,
                'start_time': self.get_start_time(tick.timestamp)})
            self.current_k_obj_idx = 0
        else:
            next_time = self.k_objs[self.current_k_obj_idx]['start_time'] + self.get_time_delta()
            time_diff = tick.timestamp - next_time
            if time_diff.total_seconds() >= 0:
                self.k_objs.append({
                    'k_open': tick.k_open,
                    'k_close': tick.k_close,
                    'k_low': tick.k_low,
                    'k_high': tick.k_high,
                    'base_amount': tick.base_amount,
                    'quote_amount': tick.quote_amount,
                    'block_num': tick.block_num,
                    'start_time': tick.timestamp
                })
                self.current_k_obj_idx += 1
            else:
                logging.debug("Update k line record: %s" % tick.timestamp)
                self.k_objs[self.current_k_obj_idx]['k_close'] = tick.k_close
                if self.k_objs[self.current_k_obj_idx]['k_low'] > tick.k_low:
                    self.k_objs[self.current_k_obj_idx]['k_low'] = tick.k_low
                if self.k_objs[self.current_k_obj_idx]['k_high'] < tick.k_high:
                    self.k_objs[self.current_k_obj_idx]['k_high'] = tick.k_high
                self.k_objs[self.current_k_obj_idx]['base_amount'] += tick.base_amount
                self.k_objs[self.current_k_obj_idx]['quote_amount'] += tick.quote_amount


class KLine15MinObj(KLine5MinObj):
    def __init__(self, k_obj):
        logging.debug("KLine15MinObj created")
        KLine5MinObj.__init__(self, k_obj) 
        self.cycle_of_base = 15


class KLine30MinObj(KLine5MinObj):
    def __init__(self, k_obj):
        logging.debug("KLine30MinObj created")
        KLine5MinObj.__init__(self, k_obj) 
        self.cycle_of_base = 30


class KLine1HourObj(KLine5MinObj):
    def __init__(self, k_obj):
        logging.debug("KLine1HourObj created")
        KLine1MinObj.__init__(self, k_obj) 
        self.cycle_of_base = 60


    def get_start_time(self, start_time):
        return start_time.replace(minute=0, second=0, microsecond=0)


# Hour based K-Line data is based on 1-Hour K-line data
class KLine2HourObj(KLine1HourObj):
    def __init__(self, k_obj):
        logging.debug("KLine2HourObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 2


    def get_start_time(self, start_time):
        hour = start_time.hour - start_time.hour % self.cycle_of_base
        return start_time.replace(hour=hour, minute=0, second=0, microsecond=0)


    def get_time_delta(self):
        return datetime.timedelta(hours=self.cycle_of_base)


class KLine6HourObj(KLine2HourObj):
    def __init__(self, k_obj):
        logging.debug("KLine6HourObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 6


class KLine12HourObj(KLine2HourObj):
    def __init__(self, k_obj):
        logging.debug("KLine12HourObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 12


class KLineDailyObj(KLine2HourObj):
    def __init__(self, k_obj):
        logging.debug("KLineDailyObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 24


    def get_start_time(self, start_time):
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0)


class KLineWeeklyObj(KLineDailyObj):
    def __init__(self, k_obj):
        logging.debug("KLineWeeklyObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 24 * 7


    def get_start_time(self, start_time):
        weekday = start_time.weekday()
        return start_time.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=weekday)


class KLineMonthlyObj(KLineDailyObj):
    def __init__(self, k_obj):
        logging.debug("KLineWeeklyObj created")
        KLine1HourObj.__init__(self, k_obj) 
        self.cycle_of_base = 30


    def get_time_delta(self):
        return datetime.timedelta(days=self.cycle_of_base)

