import fjordkraft as fk

values = fk.read_api()
print(values)
fk.write_to_database(values)