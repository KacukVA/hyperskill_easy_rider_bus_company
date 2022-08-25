import json
import re


class BusRoute:
    start_stops = set()
    finish_stops = set()
    unique_stops = set()
    all_stops = list()
    transfer_stops = set()
    S = 0
    F = 0

    def __init__(self, _bus_id):
        self.bus_id = _bus_id
        self.stop_name = set()
        self.start_stop_name = set()
        self.finish_stop_name = set()
        self.on_demand_stop_name = set()
        self._current_index = 0


class Validate:
    def __set_name__(self, owner, name):
        self.name = '_' + name

    def __get__(self, instance, owner):
        return getattr(instance, self.name)


class ValidateBusID(Validate):
    error = 0

    @classmethod
    def verify(cls, value):
        if value is None or type(value) != int:
            cls.error += 1

    def __set__(self, instance, value):
        self.verify(value)
        setattr(instance, self.name, self.error)


class ValidateStopID(ValidateBusID):
    error = 0


class ValidateStopName(ValidateBusID):
    error = 0

    @classmethod
    def verify(cls, value):
        # print(value)
        if value == '' or type(value) != str:
            cls.error += 1
        match = re.match(r'[A-Z].+ (Road|Avenue|Boulevard|Street)$', value)
        if not match:
            # print(value)
            cls.error += 1


class ValidateNextStop(ValidateBusID):
    error = 0


class ValidateStopType(Validate):
    error = 0

    @classmethod
    def verify(cls, value):
        if type(value) != str:
            cls.error += 1
        elif value == '':
            return
        elif len(re.findall(r'[SOF]', value)) != 1:
            cls.error += 1

    def __set__(self, instance, value):
        self.verify(value)
        setattr(instance, self.name, self.error)


class ValidateATime(Validate):
    error = 0

    @classmethod
    def verify(cls, value):
        if value is None or type(value) != str:
            cls.error += 1
        elif not re.findall(r'([01]\d|2[0-4]):([0-5]\d|60)', value):
            cls.error += 1
        elif len(value) != 5:
            cls.error += 1

    def __set__(self, instance, value):
        self.verify(value)
        setattr(instance, self.name, self.error)


class Validator:
    bus_id_error = ValidateBusID()
    stop_id_error = ValidateStopID()
    stop_name_error = ValidateStopName()
    next_stop_error = ValidateNextStop()
    stop_type_error = ValidateStopType()
    a_time_error = ValidateATime()

    def __init__(self, *args):
        self.bus_id_error = args[0][0]
        self.stop_id_error = args[0][1]
        self.stop_name_error = args[0][2]
        self.next_stop_error = args[0][3]
        self.stop_type_error = args[0][4]
        self.a_time_error = args[0][5]

    def __str__(self):
        self.result = self.stop_type_error + self.stop_name_error + self.a_time_error
        return f'''
        Type and required field validation: {self.result} errors
        stop_name: {self.stop_name_error}
        stop_type: {self.stop_type_error}
        a_time: {self.a_time_error}
        '''


def print_bus_info(dictionary: dict):
    print('Line names and number of stops:')
    for key, value in dictionary.items():
        print(f'bus_id: {key}, stops: {value}')


def get_bus_id(d_text) -> set:
    buses_id = set()
    for _ in d_text:
        buses_id.add(_['bus_id'])
    return buses_id


def validate_stopes(_routes):
    for _ in _routes:
        if _.S != 1 or _.F != 1:
            print(f'There is no start or end stop for the line: {_.bus_id}.')
            return False
    return True


def init_validator(data):
    obj = None
    for _ in data:
        obj = Validator(list(_.values()))
    return obj


def get_bus_line_info(data) -> dict:
    buses_lines_info = {}
    for _ in data:
        if buses_lines_info.get(_['bus_id']):
            buses_lines_info[_['bus_id']] += 1
        else:
            buses_lines_info[_['bus_id']] = 1
    return buses_lines_info


def validate_bus_line_condition(data):
    bus_id = get_bus_id(data)
    bus_routes = set()
    for bus in bus_id:
        route = BusRoute(bus)
        bus_routes.add(route)
        for _ in data:
            if bus == _['bus_id']:
                route.stop_name.add(_['stop_name'])
                if _['stop_type'] == 'S':
                    route.S = route.S + 1
                    route.start_stop_name.add(_['stop_name'])
                if _['stop_type'] == 'F':
                    route.F = route.F + 1
                    route.finish_stop_name.add(_['stop_name'])
                if _['stop_type'] == 'O':
                    route.on_demand_stop_name.add(_['stop_name'])
    for _ in data:
        if _['stop_type'] == 'S':
            BusRoute.start_stops.add(_['stop_name'])
        if _['stop_type'] == 'F':
            BusRoute.finish_stops.add(_['stop_name'])
        BusRoute.unique_stops.add(_['stop_name'])
        BusRoute.all_stops.append(_['stop_name'])
    for stop in BusRoute.unique_stops:
        if BusRoute.all_stops.count(stop) > 1:
            BusRoute.transfer_stops.add(stop)
    return bus_routes


def print_bus_routes(routes_set):
    if validate_stopes(routes_set):
        print(f"""
        Start stops: {len(BusRoute.start_stops)} {sorted(list(BusRoute.start_stops))}
        Transfer stops: {len(BusRoute.transfer_stops)} {sorted(list(BusRoute.transfer_stops))}
        Finish stops: {len(BusRoute.finish_stops)} {sorted(list(BusRoute.finish_stops))}
        """)


def convert_time_to_sec(dd_mm):
    minutes, seconds = 60, 60
    total_seconds = 0

    if dd_mm[0] == '0':
        total_seconds += int(dd_mm[1]) * minutes * seconds
    else:
        total_seconds += int(dd_mm[:2]) * minutes * seconds

    if dd_mm[3] == '0':
        total_seconds += int(dd_mm[3]) * seconds
    else:
        total_seconds += int(dd_mm[3:5]) * seconds

    return total_seconds


def validate_time_line(data):
    result = []
    buses_id = get_bus_id(data)
    for bus in buses_id:
        current_time = 0
        for _ in data:
            if _['bus_id'] == bus:
                a_time = convert_time_to_sec(_['a_time'])
                if current_time >= a_time:
                    result.append(_)
                    break
                else:
                    current_time = a_time

    print_validate_time_line(result)


def print_validate_time_line(data):
    print('Arrival time test:')
    if len(data) == 0:
        print('OK')
    else:
        for _ in data:
            print(f"bus_id line {str(_['bus_id'])}: wrong time on station {_['stop_name']}")


def validate_on_demand(routes_set):
    result = list()
    for rout in routes_set:
        for stop in rout.on_demand_stop_name:
            if stop in rout.finish_stop_name:
                result.append(stop)
            if stop in rout.start_stop_name:
                result.append(stop)
            if stop in rout.transfer_stops:
                result.append(stop)

    return result


def print_on_demand(on_demand_list):
    print('On demand stops test:')
    if len(on_demand_list) == 0:
        print('OK')
    else:
        print(f'Wrong stop type: {sorted(on_demand_list)}')


if __name__ == '__main__':
    text = input()
    deserialized_text = json.loads(text)

    validator = init_validator(deserialized_text)
    # print(validator)

    bus_line_info = get_bus_line_info(deserialized_text)
    # print_bus_info(bus_line_info)

    routes = validate_bus_line_condition(deserialized_text)
    # print_bus_routes(routes)

    # validate_time_line(deserialized_text)

    on_demand_test = validate_on_demand(routes)
    print_on_demand(on_demand_test)
