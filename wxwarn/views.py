from djangomako.shortcuts import render_to_response

def home(request):
    """
    GET /

    Show the home page
    """
    return render_to_response('index.html', {})