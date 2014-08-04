def run(views, view_data):
    count = len(views)
    for v in views:
        view_data.append((count, v))
        count -= 1
