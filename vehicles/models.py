from django.db import models
from django.contrib.auth.models import User, AbstractUser
from vehicles.storage_backends import MediaStorage


class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(storage=MediaStorage(), upload_to='vehicle_posts/', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Review(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.vehicle.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(storage=MediaStorage(), upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
class Collection(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    vehicles = models.ManyToManyField(Vehicle, related_name='collections')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False)
    users_with_access = models.ManyToManyField(User, related_name='accessible_collections', blank=True)

    def __str__(self):
        return self.name

class CollectionRequest(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Request by {self.user.username} for {self.collection.name}"
    
class VehicleRequest(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Request by {self.user.username} for {self.vehicle.name}"