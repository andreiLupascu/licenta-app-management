def pdf_file_check(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'
