from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookForm, CharacterChoiceForm
from .gemini_client import generate_characters, generate_chapter_and_options
from .models import AdventureSession, Chapter
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import SignupForm, LoginForm
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

# --- New Views ---

@login_required
def my_adventures(request):
    """List all saved adventures for the logged-in user."""
    sessions = AdventureSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "adventure/my_adventures.html", {"sessions": sessions})

@login_required
def resume_adventure(request, session_id):
    """Set the session ID and redirect to the reader."""
    session = get_object_or_404(AdventureSession, id=session_id, user=request.user)
    request.session["adventure_session_id"] = session.id
    return redirect("read_chapter")

def read_chapter(request):
    """
    Renders the *current* latest chapter for the session.
    Used for resuming a game or rendering after 'Go Back'.
    """
    session_id = request.session.get("adventure_session_id")
    session = get_object_or_404(AdventureSession, id=session_id)
    
    # Get the latest chapter based on order
    chapter = session.chapters.order_by("-order").first()
    
    # If no chapters exist (shouldn't happen in valid session), go home
    if not chapter:
        return redirect("index")
        
    return render(request, "adventure/reader.html", {"session": session, "chapter": chapter})

def go_back(request):
    """
    'Undo' the last move by deleting the current chapter.
    """
    session_id = request.session.get("adventure_session_id")
    session = get_object_or_404(AdventureSession, id=session_id)
    
    # Get the latest chapter
    current_chapter = session.chapters.order_by("-order").first()
    
    if current_chapter:
        # Only allow going back if we are NOT at the very first chapter (order 1)
        if current_chapter.order > 1:
            current_chapter.delete()
        else:
            # Optional: If they go back at Chapter 1, maybe show an alert or redirect home?
            pass 
            
    return redirect("read_chapter")

# For JWT token generation we prefer using djangorestframework-simplejwt. If it's not installed
# you can install it with:
#   pip install djangorestframework-simplejwt
try:
    from rest_framework_simplejwt.tokens import RefreshToken
    SIMPLEJWT_AVAILABLE = True
except Exception:
    SIMPLEJWT_AVAILABLE = False

def index(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data["book_title"]
            # call Gemini to get top 5 characters
            try:
                characters = generate_characters(book, top_k=5)
            except Exception as e:
                characters = []
            # store session
            session = AdventureSession.objects.create(user=request.user if request.user.is_authenticated else None, book_title=book)
            request.session["adventure_session_id"] = session.id
            return render(request, "adventure/choose_character.html", {"book": book, "characters": characters})
    else:
        form = BookForm()
    return render(request, "adventure/index.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data.get("email")
            password = form.cleaned_data["password"]
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already taken')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                login(request, user)
                return redirect('/')
    else:
        form = SignupForm()
    return render(request, "adventure/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # If simplejwt available, return JWT tokens as JSON as well
                if SIMPLEJWT_AVAILABLE:
                    refresh = RefreshToken.for_user(user)
                    return JsonResponse({"access": str(refresh.access_token), "refresh": str(refresh)})
                return redirect('/')
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, "adventure/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('/')


def token_obtain_pair(request):
    """A simple endpoint to obtain JWT tokens (POST with username/password). Requires simplejwt."""
    if not SIMPLEJWT_AVAILABLE:
        return JsonResponse({"detail": "simplejwt not installed"}, status=500)
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)
    # Support both form-encoded and JSON
    username = request.POST.get('username')
    password = request.POST.get('password')
    if not username or not password:
        try:
            import json
            body = json.loads(request.body)
            username = body.get('username')
            password = body.get('password')
        except Exception:
            pass
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    refresh = RefreshToken.for_user(user)
    return JsonResponse({"access": str(refresh.access_token), "refresh": str(refresh)})


from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except Exception:
    JWTAuthentication = None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication] if JWTAuthentication is not None else [])
def profile_api(request):
    """Return the authenticated user's minimal profile (requires JWT auth).
    Note: This endpoint requires djangorestframework-simplejwt to be installed and configured.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
    return JsonResponse({"username": user.username, "email": user.email, "date_joined": user.date_joined})

def choose_character(request):
    if request.method == "POST":
        char = request.POST.get("character")
        session_id = request.session.get("adventure_session_id")
        session = get_object_or_404(AdventureSession, id=session_id)
        session.chosen_character = char
        session.save()
        # generate first chapter
        gen = generate_chapter_and_options(session.book_title, char, prev_context="")
        chapter = Chapter.objects.create(session=session, text=gen["chapter_text"], options=gen["options"], order=1)
        return render(request, "adventure/reader.html", {"session": session, "chapter": chapter})
    return redirect("/")

def follow_option(request, option_id):
    """
    Called when user chooses one of the 3 options. We'll generate the next chapter incorporating
    the previous chapter as context.
    """
    session_id = request.session.get("adventure_session_id")
    session = get_object_or_404(AdventureSession, id=session_id)
    last_chapter = session.chapters.order_by("-order").first()
    try:
        option_text = next((o["text"] for o in last_chapter.options if str(o.get("id")) == str(option_id)), "")
    except Exception:
        option_text = ""
    # create prompt context from last chapter + chosen option
    prev_context = f"Previous chapter: {last_chapter.text}\nUser chose: {option_text}"
    gen = generate_chapter_and_options(session.book_title, session.chosen_character, prev_context=prev_context)
    chapter = Chapter.objects.create(session=session, text=gen["chapter_text"], options=gen["options"], order=last_chapter.order+1)
    return render(request, "adventure/reader.html", {"session": session, "chapter": chapter})
