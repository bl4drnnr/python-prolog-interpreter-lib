class ApiResponse(Exception):
    def __init__(self, response, status_code=200):
        self.response = {"data": response, "statusCode": status_code}
        self.status_code = status_code


class SingleArgument(ApiResponse):
    pass


class WrongOption(ApiResponse):
    pass


class WrongJsonFormat(ApiResponse):
    def __init__(self, response="Wrong JSON format", status_code=500):
        super().__init__(response, status_code)


class WrongFactFormat(ApiResponse):
    def __init__(self, response="Wrong fact format", status_code=500):
        super().__init__(response, status_code)


class WrongPrologFormat(ApiResponse):
    pass
