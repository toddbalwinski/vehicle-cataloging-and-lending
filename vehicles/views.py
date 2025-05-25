from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from vehicles.models import Vehicle
from django.shortcuts import get_object_or_404
from vehicles.forms import VehicleForm, ReviewForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from .models import Collection, UserProfile, CollectionRequest, VehicleRequest
from .forms import ProfilePictureForm, VehicleSearchForm
from django.contrib.auth.models import AnonymousUser, User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileEditForm
import uuid

from django.conf import settings


def landing(request):
    if request.user.is_authenticated:
        return redirect('vehicles:home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('vehicles:home')
        else:
            pass
    return render(request, 'vehicles/landing.html')

def guest_login(request):
    request.session['guest'] = True
    request.session['guest_id'] = str(uuid.uuid4())
    request.user = AnonymousUser()
    return redirect('vehicles:home')

def home(request):
    vehicles = Vehicle.objects.all()
    is_guest = request.session.get('guest', False)
    user_type = 'guest'
    # if not is_guest and request.user.is_authenticated:
    if request.user.is_authenticated:
        if not hasattr(request.user, 'userprofile'):
            UserProfile.objects.create(user=request.user)
        
        if request.user.groups.filter(name='Librarian').exists():
            user_type = 'librarian'
        else:
            user_type = 'patron'
    
    search_form = VehicleSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data['query']
        if query:
            vehicles = vehicles.filter(name__icontains=query) | vehicles.filter(description__icontains=query)

    private_collections = user_requests = []
    if user_type == 'guest':
        collections = Collection.objects.filter(is_private=False)
    elif user_type == 'patron':
        collections = Collection.objects.filter(is_private=False) | Collection.objects.filter(users_with_access=request.user) | Collection.objects.filter(owner=request.user)
        private_collections = [c for c in Collection.objects.filter(is_private=True).difference(Collection.objects.filter(users_with_access=request.user) | Collection.objects.filter(owner=request.user))]
        user_requests = CollectionRequest.objects.filter(user=request.user).values_list('collection_id', flat=True)
    else:
        collections = Collection.objects.all()


    return render(request, 'vehicles/home.html', {
        'vehicles': vehicles,
        'user_type': user_type,
        'search_form': search_form,
        'is_guest': is_guest,
        'collections': collections,
        'private_collections': private_collections,
        'user_requests': user_requests,
    })

def vehicle_detail(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.vehicle = vehicle
            review.user = request.user
            review.save()
            return redirect('vehicles:vehicle_detail', vehicle_id=vehicle.id)
    else:
        form = ReviewForm()

    reviews = vehicle.reviews.all()

    context = {
        'vehicle': vehicle,
        'reviews': reviews,
        'form': form,
    }

    return render(request, 'vehicles/vehicle_detail.html', context)

@login_required
def manage_vehicles(request):
    if not request.user.groups.filter(name='Librarian').exists():
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    vehicles = Vehicle.objects.all()

    return render(request, 'vehicles/manage_vehicles.html', {'vehicles': vehicles})

@login_required
def add_vehicle(request):
    if not request.user.groups.filter(name='Librarian').exists():
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user 
            collections = form.cleaned_data['collections']
            
            private_collections = [collection for collection in collections if collection.is_private]
            
            if private_collections:
                if len(collections) > 1:
                    form.add_error('collections', 'A vehicle in a private collection can only belong to that collection.')
                    return render(request, 'vehicles/add_vehicle.html', {'form': form})
            
            vehicle.save() 
            form.save_m2m() 
            return redirect('vehicles:manage_vehicles') 
    else:
        form = VehicleForm(user=request.user)
    # NEED TO FILTER COLLECTIONS DEPENDING ON WHETHER PATRON OR LIBRARIAN - ANDY
    collections = Collection.objects.all()
    return render(request, 'vehicles/add_vehicle.html', {'form': form, 'collections': collections})

@login_required
def edit_vehicle(request, vehicle_id):
    if not request.user.groups.filter(name='Librarian').exists():
        return HttpResponseForbidden("You do not have permission to access this page.")
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        vehicle.name = request.POST.get('name')
        vehicle.description = request.POST.get('description')
        image = request.FILES.get('image')
        if image:
            vehicle.image = image
        vehicle.available = request.POST.get('available') == 'on'
        selected_collections = request.POST.getlist('collections')
        vehicle.collections.set(Collection.objects.filter(id__in=selected_collections))
        vehicle.save()
        return redirect('vehicles:manage_vehicles')
    # NEED TO FILTER COLLECTIONS DEPENDING ON WHETHER PATRON OR LIBRARIAN - ANDY
    collections = Collection.objects.all()
    return render(request, 'vehicles/edit_vehicle.html', {'vehicle': vehicle, 'collections': collections})

@login_required
def delete_vehicle(request, vehicle_id):
    if not request.user.groups.filter(name='Librarian').exists():
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == 'POST':
        vehicle.delete()
        return redirect('vehicles:manage_vehicles')
    
    return HttpResponseForbidden("Invalid request method.")

def login_view(request):
    if request.user.is_authenticated:
        print(request.user)
        return redirect('/home')  

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                profile, created = UserProfile.objects.get_or_create(user=user)

                # Check for missing fields
                missing_fields = []
                if not user.first_name or not user.first_name.strip():
                    missing_fields.append('first_name')
                if not user.last_name or not user.last_name.strip():
                    missing_fields.append('last_name')
                if not user.username or not user.username.strip():
                    missing_fields.append('username')
                if not profile.profile_picture:
                    missing_fields.append('profile_picture')

                if missing_fields:
                    messages.info(request, 'Please complete your profile information.')
                    return redirect('vehicles:complete_profile')
                
                if 'guest' in request.session:
                    del request.session['guest']
                    del request.session['guest_id']

                return redirect('/home')
            
            else:
                return HttpResponse('Invalid login credentials', status=401)
        
        else:
            return render(request, 'registration/login.html', {'form': form})
    
    else:
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    if 'guest' in request.session:
        del request.session['guest']
        del request.session['guest_id']
    
    logout(request)
    return redirect('vehicles:landing')

@login_required
def complete_profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Determine which fields are missing
    missing_fields = []
    if not request.user.first_name or not request.user.first_name.strip():
        missing_fields.append('first_name')
    if not request.user.last_name or not request.user.last_name.strip():
        missing_fields.append('last_name')
    if not request.user.username or not request.user.username.strip():
        missing_fields.append('username')
    if not profile.profile_picture:
        missing_fields.append('profile_picture')

    if request.method == 'POST':
        # Update user fields if they were missing
        if 'first_name' in missing_fields:
            request.user.first_name = request.POST.get('first_name', '').strip()
        if 'last_name' in missing_fields:
            request.user.last_name = request.POST.get('last_name', '').strip()
        if 'username' in missing_fields:
            request.user.username = request.POST.get('username', '').strip()
        if 'profile_picture' in missing_fields and 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        request.user.save()
        profile.save()
        
        return redirect('vehicles:home')

    return render(request, 'vehicles/complete_profile.html', {
        'missing_fields': missing_fields,
        'current_username': request.user.username,
        'current_first_name': request.user.first_name,
        'current_last_name': request.user.last_name,
    })


@login_required
def profile(request):
    # Ensure the UserProfile is created for the user if it doesn't exist
    if not hasattr(request.user, 'userprofile'):
        UserProfile.objects.create(user=request.user)

    profile_form = ProfilePictureForm(instance=request.user.userprofile)
    user_form = ProfileEditForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'profile_picture_submit' in request.POST:
            profile_form = ProfilePictureForm(request.POST, request.FILES, instance=request.user.userprofile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile picture updated successfully!')
                return redirect('vehicles:profile')
                
        elif 'user_info_submit' in request.POST:
            user_form = ProfileEditForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile information updated successfully!')
                return redirect('vehicles:profile')
                
        elif 'password_change_submit' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully!')
                return redirect('vehicles:profile')
            else:
                messages.error(request, 'Please correct the error below.')

    return render(request, 'vehicles/profile.html', {
        'profile_form': profile_form,
        'user_form': user_form,
        'password_form': password_form,
        'user': request.user,
        'MEDIA_URL': settings.MEDIA_URL
    })

#test comment
def test(request):
    pass

@login_required
def manage_collections(request):
    user_type = 'patron'
    collection_requests = []
    if request.user.groups.filter(name='Librarian').exists():
        collections = Collection.objects.all()
        user_type = 'librarian'
        collection_requests = CollectionRequest.objects.all()
    else:
        collections = Collection.objects.filter(owner=request.user)
    return render(request, 'vehicles/manage_collections.html', {'collections': collections, 'user_type': user_type, 'collection_requests': collection_requests})

@login_required
def add_collection(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_private = 'is_private' in request.POST

        new_collection = Collection(
            name=name,
            description=description,
            is_private=is_private,
            owner=request.user
        )
        new_collection.save()
        return redirect('vehicles:manage_collections') 

    return redirect('vehicles:manage_collections')

@login_required
def edit_collection(request, collection_id):
    user_type = 'patron'
    if request.user.groups.filter(name='Librarian').exists():
        collection = get_object_or_404(Collection, id=collection_id)
        user_type = 'librarian'
    else:
        collection = get_object_or_404(Collection, id=collection_id, owner=request.user)

    if request.method == 'POST':
        collection.name = request.POST.get('name')
        collection.description = request.POST.get('description')
        collection.is_private = 'is_private' in request.POST
        if not collection.is_private:
            CollectionRequest.objects.filter(collection=collection).delete()
        collection.save()
        return redirect('vehicles:manage_collections')

    return render(request, 'vehicles/edit_collection.html', {'collection': collection, 'user_type': user_type})

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)

    if request.method == 'POST':
        collection.delete()
        return redirect('vehicles:manage_collections')

    return HttpResponseForbidden("Invalid request method.")

def collection_details(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    vehicles = collection.vehicles.all()
    user_type = 'guest'
    if request.user.is_authenticated:
        user_type = 'patron'
    if request.user.groups.filter(name='Librarian').exists():
        user_type = 'librarian'
    if collection.is_private and user_type == 'guest':
        return HttpResponseForbidden("You do not have permission to access this collection.")
    if user_type == 'patron':
        if collection.is_private and request.user not in collection.users_with_access.all() and request.user != collection.owner:
            return HttpResponseForbidden("You do not have permission to access this collection.")
    return render(request, 'vehicles/collection_details.html', {'collection': collection, 'vehicles': vehicles, 'user_type': user_type})

@login_required
def create_request(request, collection_id):
    if request.method == 'POST':
        collection = get_object_or_404(Collection, id=collection_id)
        user = request.user
        if CollectionRequest.objects.filter(collection=collection, user=user).exists():
            return redirect('vehicles:home')
        new_request = CollectionRequest(
            collection=collection,
            user=user,
        )
        new_request.save()
        return redirect('vehicles:home') 

    return redirect('vehicles:home')

@login_required
def approve_request(request, request_id):
    collection_request = get_object_or_404(CollectionRequest, id=request_id)
    if request.method == 'POST':
        collection = collection_request.collection
        user = collection_request.user
        collection.users_with_access.add(user)
        collection_request.delete()
        return redirect('vehicles:manage_collections') 

    return redirect('vehicles:manage_collections')

@login_required
def reject_request(request, request_id):
    collection_request = get_object_or_404(CollectionRequest, id=request_id)
    if request.method == 'POST':
        collection_request.delete()
        return redirect('vehicles:manage_collections') 

    return redirect('vehicles:manage_collections')

@login_required
def manage_librarians(request):
    if request.user.groups.filter(name='Librarian').exists():
        librarian_group = Group.objects.get(name='Librarian')
        patrons = User.objects.exclude(groups=librarian_group)

        return render(request, 'vehicles/manage_librarians.html', {'patrons': patrons})
    else:
        return HttpResponseForbidden("You do not have permission to access this page.")

@login_required
def promote_to_librarian(request, user_id):
    if request.method == 'POST' and request.user.groups.filter(name='Librarian').exists():
        user = get_object_or_404(User, id=user_id)
        librarian_group, _ = Group.objects.get_or_create(name='Librarian')
        user.groups.add(librarian_group)
        return redirect('vehicles:manage_librarians')
    else:
        return HttpResponseForbidden("You do not have permission to perform this action.")
    
@login_required
def borrow_vehicle(request, vehicle_id):
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        user = request.user
        if VehicleRequest.objects.filter(vehicle=vehicle, user=user).exists():
            return redirect('vehicles:home')
        new_request = VehicleRequest(
            vehicle=vehicle,
            user=user,
        )
        new_request.save()
        return redirect('vehicles:home') 
    return redirect('vehicles:home')

@login_required
def manage_requests(request):
    if request.user.groups.filter(name='Librarian').exists():
        vehicle_requests = VehicleRequest.objects.all()
        return render(request, 'vehicles/manage_requests.html', {'vehicle_requests': vehicle_requests})
    else:
        return HttpResponseForbidden("You do not have permission to access this page.")
    
@login_required
def approve_borrow(request, request_id):
    if request.method == 'POST':
        vehicle_request = get_object_or_404(VehicleRequest, id=request_id)
        vehicle = vehicle_request.vehicle
        # user = vehicle_request.user
        # vehicle.borrowed_by = user
        vehicle.available = False
        vehicle.save()
        vehicle_request.delete()
        return redirect('vehicles:manage_requests') 

    return redirect('vehicles:manage_requests')

@login_required
def reject_borrow(request, request_id):
    if request.method == 'POST':
        vehicle_request = get_object_or_404(VehicleRequest, id=request_id)
        vehicle_request.delete()
        return redirect('vehicles:manage_requests') 

    return redirect('vehicles:manage_requests')