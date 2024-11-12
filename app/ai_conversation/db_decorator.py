def entity(clazz):
    code = clazz.__init__.__code__

    @staticmethod
    def load_from_db(row):
        dictionary = {
            code.co_varnames[i]: row[code.co_varnames[i]]
            for i in range(1, code.co_argcount)
        }
        return clazz(**dictionary)

    clazz.load_from_db = load_from_db
    return clazz
