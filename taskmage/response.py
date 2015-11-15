from tabulate import tabulate

class Response():
    message = None;
    data = None;

    def print(self):
        if self.message:
            if type(self.message) == "str":
                print(self.message)

            elif type(self.message) == "list":
                for message in self.message:
                    print("{}\n".format(message))

        elif (self.data):
            print(tabulate(self.data["rows"], headers=self.data["headers"]))


