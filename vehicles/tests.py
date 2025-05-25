from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from vehicles.models import (
    Vehicle, Review, UserProfile,
    Collection, CollectionRequest, VehicleRequest
)
from vehicles.forms import (
    VehicleForm, ReviewForm,
    VehicleSearchForm, CollectionForm
)

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='testpass123')
        self.profile = UserProfile.objects.create(user=self.user)
        self.vehicle = Vehicle.objects.create(
            name='Car1', description='Nice car', owner=self.user
        )
        self.collection = Collection.objects.create(
            name='Col1', description='Desc', owner=self.user
        )
        self.collection.vehicles.add(self.vehicle)
        self.review = Review.objects.create(
            vehicle=self.vehicle, user=self.user,
            rating=5, comment='Great'
        )
        self.coll_req = CollectionRequest.objects.create(
            collection=self.collection, user=self.user
        )
        self.veh_req = VehicleRequest.objects.create(
            vehicle=self.vehicle, user=self.user
        )

    def test_vehicle_str_and_defaults(self):
        self.assertEqual(str(self.vehicle), 'Car1')
        self.assertTrue(self.vehicle.available)

    def test_review_str(self):
        exp = f"Review by {self.user.username} on {self.vehicle.name}"
        self.assertEqual(str(self.review), exp)

    def test_userprofile_str(self):
        self.assertEqual(str(self.profile), self.user.username)

    def test_collection_str_and_association(self):
        self.assertEqual(str(self.collection), 'Col1')
        self.assertIn(self.vehicle, self.collection.vehicles.all())

    def test_request_strings(self):
        exp_c = f"Request by {self.user.username} for {self.collection.name}"
        exp_v = f"Request by {self.user.username} for {self.vehicle.name}"
        self.assertEqual(str(self.coll_req), exp_c)
        self.assertEqual(str(self.veh_req), exp_v)


class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user2', password='pass2')
        self.pub = Collection.objects.create(
            name='Public', description='D', owner=self.user, is_private=False
        )
        self.priv = Collection.objects.create(
            name='Private', description='D', owner=self.user, is_private=True
        )

    def test_vehicleform_filters_collections(self):
        form = VehicleForm(user=self.user)
        qs = form.fields['collections'].queryset
        self.assertIn(self.pub, qs)
        self.assertIn(self.priv, qs)

    def test_other_forms(self):
        rform = ReviewForm()
        self.assertIn('rating', rform.fields)
        cform = CollectionForm(data={'name': 'C', 'description': 'D', 'is_private': True})
        self.assertTrue(cform.is_valid())
        sf_empty = VehicleSearchForm(data={})
        self.assertTrue(sf_empty.is_valid())
        sf_query = VehicleSearchForm(data={'query': 'Search'})
        self.assertTrue(sf_query.is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewuser', password='pass')
        self.librarian = User.objects.create_user(username='librarian', password='pass')
        self.l_group = Group.objects.create(name='Librarian')
        self.librarian.groups.add(self.l_group)
        self.vehicle = Vehicle.objects.create(
            name='Car2', description='Desc', owner=self.librarian
        )

    def test_landing_and_auth_flows(self):
        r = self.client.get(reverse('vehicles:landing'))
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(reverse('vehicles:login'), {'username': 'viewuser', 'password': 'pass'})
        self.assertEqual(r2.status_code, 302)
        self.client.login(username='viewuser', password='pass')
        r3 = self.client.get(reverse('vehicles:logout'))
        self.assertEqual(r3.status_code, 302)

    def test_guest_login(self):
        r = self.client.get(reverse('vehicles:guest_login'))
        self.assertTrue(self.client.session.get('guest', False))
        self.assertEqual(r.status_code, 302)

    def test_home_page_content(self):
        r = self.client.get(reverse('vehicles:home'))
        self.assertContains(r, 'Welcome Guest')
        self.client.login(username='viewuser', password='pass')
        r2 = self.client.get(reverse('vehicles:home'))
        self.assertContains(r2, 'Available Vehicles')

    def test_manage_vehicles_permissions(self):
        self.client.login(username='viewuser', password='pass')
        r = self.client.get(reverse('vehicles:manage_vehicles'))
        self.assertEqual(r.status_code, 403)
        self.client.login(username='librarian', password='pass')
        r2 = self.client.get(reverse('vehicles:manage_vehicles'))
        self.assertEqual(r2.status_code, 200)

    def test_add_vehicle(self):
        self.client.login(username='librarian', password='pass')
        response = self.client.post(reverse('vehicles:add_vehicle'), {
            'name': 'NewCar', 'description': 'D', 'available': True, 'collections': []
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vehicle.objects.filter(name='NewCar').exists())

    def test_vehicle_detail_and_review(self):
        r = self.client.get(reverse('vehicles:vehicle_detail', args=[self.vehicle.id]))
        self.assertEqual(r.status_code, 200)
        self.client.login(username='viewuser', password='pass')
        r2 = self.client.post(
            reverse('vehicles:vehicle_detail', args=[self.vehicle.id]),
            {'rating': 3, 'comment': 'OK'}
        )
        self.assertEqual(r2.status_code, 302)
        self.assertTrue(Review.objects.filter(vehicle=self.vehicle, user=self.user).exists())

    def test_borrow_vehicle_request(self):
        self.client.login(username='viewuser', password='pass')
        r = self.client.post(reverse('vehicles:borrow_vehicle', args=[self.vehicle.id]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(VehicleRequest.objects.filter(vehicle=self.vehicle, user=self.user).exists())


class UrlsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='urluser', password='pass')
        self.group = Group.objects.create(name='Librarian')
        self.user.groups.add(self.group)
        self.vehicle = Vehicle.objects.create(name='URLCar', description='D', owner=self.user)

    def test_url_reverse(self):
        names = ['landing', 'home', 'login', 'logout', 'manage_vehicles', 'add_vehicle']
        for name in names:
            url = reverse(f'vehicles:{name}')
            self.assertTrue(url)
        detail = reverse('vehicles:vehicle_detail', args=[self.vehicle.id])
        self.assertTrue(detail)

class CollectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patron = User.objects.create_user(username='patron', password='pass')
        self.lib = User.objects.create_user(username='lib', password='pass')
        grp = Group.objects.create(name='Librarian')
        self.lib.groups.add(grp)
        self.pub = Collection.objects.create(
            name='Pub', description='D', owner=self.patron, is_private=False
        )
        self.priv = Collection.objects.create(
            name='Priv', description='D', owner=self.lib, is_private=True
        )
        self.req = CollectionRequest.objects.create(collection=self.priv, user=self.patron)

    def test_manage_collections_view(self):

        self.client.login(username='patron', password='pass')
        r = self.client.get(reverse('vehicles:manage_collections'))
        self.assertContains(r, 'Pub')
        self.assertNotContains(r, 'Priv')

        self.client.login(username='lib', password='pass')
        r2 = self.client.get(reverse('vehicles:manage_collections'))
        self.assertContains(r2, 'Pub')
        self.assertContains(r2, 'Priv')

    def test_add_edit_delete_collection(self):
        self.client.login(username='patron', password='pass')

        r = self.client.post(reverse('vehicles:add_collection'), {
            'name': 'New', 'description': 'D', 'is_private': False
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Collection.objects.filter(name='New').exists())
        col = Collection.objects.get(name='New')

        r2 = self.client.post(reverse('vehicles:edit_collection', args=[col.id]), {
            'name': 'Edit', 'description': 'E', 'is_private': True
        })
        self.assertEqual(r2.status_code, 302)
        col.refresh_from_db()
        self.assertTrue(col.is_private)

        r3 = self.client.post(reverse('vehicles:delete_collection', args=[col.id]))
        self.assertEqual(r3.status_code, 302)
        self.assertFalse(Collection.objects.filter(id=col.id).exists())

    def test_collection_request_workflow(self):
        self.client.login(username='patron', password='pass')
        cr = self.client.post(reverse('vehicles:create_request', args=[self.priv.id]))
        self.assertEqual(cr.status_code, 302)
        self.assertTrue(CollectionRequest.objects.filter(user=self.patron, collection=self.priv).exists())

        self.client.login(username='lib', password='pass')
        r = self.client.post(reverse('vehicles:approve_request', args=[self.req.id]))
        self.assertFalse(CollectionRequest.objects.filter(id=self.req.id).exists())
        self.assertIn(self.patron, self.priv.users_with_access.all())

        req2 = CollectionRequest.objects.create(collection=self.priv, user=self.patron)
        r2 = self.client.post(reverse('vehicles:reject_request', args=[req2.id]))
        self.assertFalse(CollectionRequest.objects.filter(id=req2.id).exists())


class LibrarianManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patron = User.objects.create_user(username='p', password='p')
        self.lib = User.objects.create_user(username='l', password='p')
        grp = Group.objects.create(name='Librarian')
        self.lib.groups.add(grp)

    def test_manage_librarians_access(self):
        self.client.login(username='p', password='p')
        r = self.client.get(reverse('vehicles:manage_librarians'))
        self.assertEqual(r.status_code, 403)
        self.client.login(username='l', password='p')
        r2 = self.client.get(reverse('vehicles:manage_librarians'))
        self.assertEqual(r2.status_code, 200)

    def test_promote_to_librarian(self):
        self.client.login(username='l', password='p')
        r = self.client.post(reverse('vehicles:promote_to_librarian', args=[self.patron.id]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(self.patron.groups.filter(name='Librarian').exists())


class BorrowApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u', password='p')
        self.lib = User.objects.create_user(username='l', password='p')
        grp = Group.objects.create(name='Librarian')
        self.lib.groups.add(grp)
        self.v = Vehicle.objects.create(name='X', description='d', owner=self.lib)
        self.req = VehicleRequest.objects.create(vehicle=self.v, user=self.user)

    def test_manage_requests_and_actions(self):
        self.client.login(username='u', password='p')
        r = self.client.get(reverse('vehicles:manage_requests'))
        self.assertEqual(r.status_code, 403)
        self.client.login(username='l', password='p')
        r2 = self.client.get(reverse('vehicles:manage_requests'))
        self.assertEqual(r2.status_code, 200)

        a = self.client.post(reverse('vehicles:approve_borrow', args=[self.req.id]))
        self.assertFalse(VehicleRequest.objects.filter(id=self.req.id).exists())
        self.v.refresh_from_db()
        self.assertFalse(self.v.available)

        req2 = VehicleRequest.objects.create(vehicle=self.v, user=self.user)
        r3 = self.client.post(reverse('vehicles:reject_borrow', args=[req2.id]))
        self.assertFalse(VehicleRequest.objects.filter(id=req2.id).exists())


class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pf', password='p')

    def test_complete_profile_flow(self):
        self.client.login(username='pf', password='p')

        r = self.client.get(reverse('vehicles:complete_profile'))
        self.assertEqual(r.status_code, 200)

        img = SimpleUploadedFile('pic.jpg', b'file', content_type='image/jpeg')
        data = {'first_name': 'First', 'last_name': 'Last'}
        r2 = self.client.post(
            reverse('vehicles:complete_profile'), data, follow=True,
            files={'profile_picture': img}
        )
        self.assertRedirects(r2, reverse('vehicles:home'))
        u = User.objects.get(username='pf')
        self.assertEqual(u.first_name, 'First')
        self.assertEqual(u.last_name, 'Last')
        self.assertTrue(hasattr(u.userprofile, 'profile_picture'))

    def test_profile_view_and_update(self):
        self.client.login(username='pf', password='p')
        r = self.client.get(reverse('vehicles:profile'))
        self.assertEqual(r.status_code, 200)

        r2 = self.client.post(
            reverse('vehicles:profile'),
            {'user_info_submit': True, 'username': 'newpf', 'email': 'a@b.com'}
        )
        self.assertRedirects(r2, reverse('vehicles:profile'))
        u = User.objects.get(id=self.user.id)
        self.assertEqual(u.username, 'newpf')
        self.assertEqual(u.email, 'a@b.com')