def pdf_file_check(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


flatten = lambda l: [item for sublist in l for item in sublist]
