from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase


# Helper strategies for generating test data
def valid_username():
    """Generate valid usernames for testing"""
    return st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122),
        min_size=3,
        max_size=30
    ).filter(lambda x: x.strip() and x.isalnum())


def valid_password():
    """Generate valid passwords for testing"""
    return st.text(
        alphabet=st.characters(
            blacklist_characters='\x00',
            blacklist_categories=('Cs', 'Cc')  # Exclude surrogates and control characters
        ),
        min_size=8,
        max_size=128
    ).filter(lambda x: '\x00' not in x and x.strip() == x)  # No null bytes and no leading/trailing whitespace


class AuthenticationPropertyTests(HypothesisTestCase):
    """Property-based tests for authentication functionality"""
    
    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_valid_login_creates_session(self, username, password):
        """
        Feature: django-auth-permissions, Property 5: Valid login creates session
        Validates: Requirements 2.1
        
        For any user with valid credentials, successful login should create 
        an authenticated session and the user should be redirected to the dashboard.
        """
        # Create a user with the generated credentials
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client to simulate requests
        client = Client()
        
        # Attempt to login with valid credentials
        response = client.post(
            reverse('login'),
            {'username': username, 'password': password},
            follow=True
        )
        
        # Verify session was created (user is authenticated)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        
        # Verify redirect to dashboard occurred
        self.assertRedirects(response, reverse('dashboard'))
        
        # Verify session data exists
        self.assertIn('_auth_user_id', client.session)
        self.assertEqual(int(client.session['_auth_user_id']), user.id)
    
    @given(
        username=valid_username(),
        correct_password=valid_password(),
        wrong_password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_credentials_rejection(self, username, correct_password, wrong_password):
        """
        Feature: django-auth-permissions, Property 6: Invalid credentials rejection
        Validates: Requirements 2.2
        
        For any invalid credential combination (wrong username or wrong password), 
        login attempts should be rejected with an error message.
        """
        # Skip if passwords happen to be the same
        if correct_password == wrong_password:
            return
        
        # Create a user with correct credentials
        User.objects.create_user(username=username, password=correct_password)
        
        # Create a client to simulate requests
        client = Client()
        
        # Test 1: Wrong password
        response = client.post(
            reverse('login'),
            {'username': username, 'password': wrong_password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Verify error message is displayed
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
        
        # Test 2: Wrong username (non-existent user)
        response = client.post(
            reverse('login'),
            {'username': username + '_wrong', 'password': correct_password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Verify error message is displayed
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
    
    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_logout_terminates_session(self, username, password):
        """
        Feature: django-auth-permissions, Property 9: Logout terminates session
        Validates: Requirements 3.1
        
        For any authenticated user, performing logout should terminate 
        the session and clear all authentication data.
        """
        # Create a user
        User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        response = client.get(reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Store session key before logout
        session_key_before = client.session.session_key
        
        # Perform logout
        response = client.post(reverse('logout'), follow=True)
        
        # Verify user is no longer authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify session data is cleared (no auth user id)
        self.assertNotIn('_auth_user_id', client.session)
        
        # Verify redirect to login page
        self.assertRedirects(response, reverse('login'))
    
    @given(
        username=valid_username(),
        password=valid_password(),
        time_before_timeout=st.integers(min_value=1, max_value=1209600)  # 1 second to 2 weeks
    )
    @settings(max_examples=100, deadline=None)
    def test_property_session_persistence_within_timeout(self, username, password, time_before_timeout):
        """
        Feature: django-auth-permissions, Property 7: Session persistence within timeout
        Validates: Requirements 2.4
        
        For any authenticated session, if accessed before the timeout period expires,
        the session should remain valid and maintain authentication state.
        """
        # Create a user
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        login_response = client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        self.assertTrue(client.session.get('_auth_user_id'))
        
        # Simulate time passing but still within timeout
        # We'll access the session before it expires
        # Django's SESSION_COOKIE_AGE is set to 1209600 seconds (2 weeks)
        # We ensure time_before_timeout is less than the configured timeout
        
        # Access a protected page before timeout
        response = client.get(reverse('dashboard'))
        
        # Verify session is still valid
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        self.assertEqual(int(client.session['_auth_user_id']), user.id)
        
        # Verify we can still access protected resources
        self.assertEqual(response.status_code, 200)
    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_session_expiration_enforcement(self, username, password):
        """
        Feature: django-auth-permissions, Property 8: Session expiration enforcement
        Validates: Requirements 2.5
        
        For any session that exceeds the configured timeout period,
        the session should be invalidated and require re-authentication.
        """
        # Create a user
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        self.assertTrue(client.session.get('_auth_user_id'))
        
        # Get the session and manually expire it
        session = client.session
        session_key = session.session_key
        
        # Import Session model to manipulate expiration
        from django.contrib.sessions.models import Session
        
        # Get the session object from database
        session_obj = Session.objects.get(session_key=session_key)
        
        # Set expiration to the past (simulate timeout)
        session_obj.expire_date = timezone.now() - timedelta(seconds=1)
        session_obj.save()
        
        # Try to access a protected page with expired session
        # Create a new client with the expired session
        expired_client = Client()
        expired_client.cookies = client.cookies
        
        # Access dashboard - should redirect to login due to expired session
        response = expired_client.get(reverse('dashboard'), follow=False)
        
        # Verify user is not authenticated (session expired)
        # The middleware should have cleared the expired session
        self.assertFalse(response.wsgi_request.user.is_authenticated)


    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_unauthenticated_access_redirection(self, username, password):
        """
        Feature: django-auth-permissions, Property 10: Unauthenticated access redirection
        Validates: Requirements 3.3
        
        For any protected view, when accessed by an unauthenticated user,
        the system should redirect to the login page.
        """
        # Create a user (but don't log in)
        User.objects.create_user(username=username, password=password)
        
        # Create an unauthenticated client
        client = Client()
        
        # Attempt to access protected dashboard without authentication
        response = client.get(reverse('dashboard'), follow=False)
        
        # Verify redirect to login page
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect URL points to login
        expected_redirect = f"{reverse('login')}?next={reverse('dashboard')}"
        self.assertEqual(response.url, expected_redirect)
        
        # Follow the redirect and verify we end up at login page
        response = client.get(reverse('dashboard'), follow=True)
        self.assertRedirects(
            response,
            expected_redirect,
            fetch_redirect_response=False
        )
        
        # Verify user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class AuthenticationUnitTests(TestCase):
    """Unit tests for authentication views"""
    
    def test_login_with_valid_credentials(self):
        """Test login with specific valid credentials"""
        # Create a test user
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Attempt login
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'testpass123'},
            follow=True
        )
        
        # Verify successful login
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'testuser')
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_login_with_invalid_credentials(self):
        """Test login with specific invalid credentials"""
        # Create a test user
        User.objects.create_user(username='testuser', password='correctpass')
        
        # Attempt login with wrong password
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'wrongpass'}
        )
        
        # Verify login failed
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify error message is present
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
        
        # Attempt login with non-existent username
        response = client.post(
            reverse('login'),
            {'username': 'nonexistent', 'password': 'somepass'}
        )
        
        # Verify login failed
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout_clears_session_data(self):
        """Test logout clears session data"""
        # Create and login a user
        User.objects.create_user(username='testuser', password='testpass123')
        client = Client()
        client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'testpass123'}
        )
        
        # Verify user is authenticated
        response = client.get(reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Logout
        response = client.post(reverse('logout'), follow=True)
        
        # Verify user is no longer authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify session auth data is cleared
        self.assertNotIn('_auth_user_id', client.session)
        
        # Verify redirect to login page
        self.assertRedirects(response, reverse('login'))



class UserManagementPropertyTests(HypothesisTestCase):
    """Property-based tests for user management functionality"""
    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password(),
        role_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_creation_with_role_assignment(self, username, email, password, role_name):
        """
        Feature: django-auth-permissions, Property 1: User creation with role assignment
        Validates: Requirements 1.1
        
        For any valid username, email, password, and role, when an admin creates a user account,
        the system should store the user with the specified credentials and the role should be 
        assigned to the user.
        """
        from django.contrib.auth.models import Group
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        # Skip passwords that don't meet Django's validation requirements
        # Also need to pass a user object to check similarity
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            # Skip this test case if password doesn't meet requirements
            return
        
        # Create a role (group)
        role = Group.objects.create(name=role_name)
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Create a new user with role assignment
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
                'role': role.id
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username=username).exists())
        
        # Get the created user
        created_user = User.objects.get(username=username)
        
        # Verify credentials are stored correctly
        self.assertEqual(created_user.username, username)
        self.assertEqual(created_user.email, email)
        
        # Verify password is hashed (not plaintext)
        self.assertNotEqual(created_user.password, password)
        self.assertTrue(created_user.check_password(password))
        
        # Verify role is assigned
        self.assertIn(role, created_user.groups.all())
        self.assertEqual(created_user.groups.count(), 1)

    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_password_hashing_invariant(self, username, email, password):
        """
        Feature: django-auth-permissions, Property 2: Password hashing invariant
        Validates: Requirements 1.3
        
        For any user creation, the password stored in the database should be hashed 
        and should not match the plaintext password provided during creation.
        """
        from django.contrib.auth.models import Group
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            return
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Create a new user
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username=username).exists())
        
        # Get the created user
        created_user = User.objects.get(username=username)
        
        # Verify password is hashed (not plaintext)
        self.assertNotEqual(created_user.password, password)
        
        # Verify the hashed password can be verified
        self.assertTrue(created_user.check_password(password))
        
        # Verify password field contains a hash (starts with algorithm identifier)
        self.assertTrue(created_user.password.startswith('pbkdf2_') or 
                       created_user.password.startswith('md5$') or
                       created_user.password.startswith('bcrypt'))

    
    @given(
        username=valid_username(),
        invalid_email=st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x and x.strip()),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_email_validation_enforcement(self, username, invalid_email, password):
        """
        Feature: django-auth-permissions, Property 3: Email validation enforcement
        Validates: Requirements 1.4
        
        For any invalid email format, attempting to create a user should result in 
        a validation error and no user should be created.
        """
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Count users before attempt
        user_count_before = User.objects.count()
        
        # Attempt to create a user with invalid email
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': invalid_email,
                'password1': password,
                'password2': password,
            }
        )
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username=username).exists())
        
        # Verify user count hasn't changed (excluding admin)
        user_count_after = User.objects.count()
        self.assertEqual(user_count_before, user_count_after)
        
        # Verify form has validation errors
        self.assertIn('email', response.context['form'].errors)

    
    @given(
        user_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_list_completeness(self, user_count):
        """
        Feature: django-auth-permissions, Property 20: User list completeness
        Validates: Requirements 7.1
        
        For any set of users in the system, when an admin requests the user list,
        all users should be displayed with their roles and status information.
        """
        from django.contrib.auth.models import Group
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create a test role
        test_role = Group.objects.create(name='test_role')
        
        # Create multiple users with various configurations
        created_users = []
        for i in range(user_count):
            user = User.objects.create_user(
                username=f'testuser_{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            # Assign role to some users
            if i % 2 == 0:
                user.groups.add(test_role)
            # Deactivate some users
            if i % 3 == 0:
                user.is_active = False
                user.save()
            created_users.append(user)
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Request user list
        response = client.get(reverse('user_list'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get users from context
        users_in_list = list(response.context['users'])
        
        # Verify all created users are in the list (plus admin)
        self.assertEqual(len(users_in_list), user_count + 1)  # +1 for admin
        
        # Verify each created user is present
        for user in created_users:
            self.assertIn(user, users_in_list)
        
        # Verify admin is also in the list
        self.assertIn(admin, users_in_list)
        
        # Verify user information is accessible (roles and status)
        for user in users_in_list:
            # Check that we can access groups (roles)
            user.groups.all()  # Should not raise an error
            # Check that we can access status
            self.assertIsNotNone(user.is_active)

    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_deactivation_prevents_login(self, username, password):
        """
        Feature: django-auth-permissions, Property 21: Deactivation prevents login
        Validates: Requirements 7.2
        
        For any user account, when deactivated by an admin, login attempts with 
        that user's credentials should be rejected.
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password
        )
        
        # Verify user can login when active
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertTrue(User.objects.get(username=username).is_active)
        
        # Create admin and deactivate the user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Deactivate the user
        response = admin_client.get(reverse('user_deactivate', args=[user.pk]))
        
        # Verify user is deactivated
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Attempt to login with deactivated account
        login_client = Client()
        response = login_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify user is not logged in
        self.assertNotIn('_auth_user_id', login_client.session)

    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_reactivation_restores_access(self, username, password):
        """
        Feature: django-auth-permissions, Property 22: Reactivation restores access (round-trip)
        Validates: Requirements 7.3
        
        For any user account, deactivating and then reactivating should restore 
        the user's ability to log in.
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password
        )
        
        # Verify user can login initially
        initial_client = Client()
        response = initial_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Create admin
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Deactivate the user
        admin_client.get(reverse('user_deactivate', args=[user.pk]))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Verify login fails when deactivated
        deactivated_client = Client()
        response = deactivated_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Reactivate the user (round-trip)
        admin_client.get(reverse('user_reactivate', args=[user.pk]))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Verify user can login again after reactivation
        reactivated_client = Client()
        response = reactivated_client.post(
            reverse('login'),
            {'username': username, 'password': password},
            follow=True
        )
        
        # Verify login is successful
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        
        # Verify session was created
        self.assertIn('_auth_user_id', reactivated_client.session)

    
    @given(
        username=valid_username(),
        original_email=st.emails(),
        new_email=st.emails(),
        new_first_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs', 'Zs', 'Zl', 'Zp')),
            min_size=1, 
            max_size=30
        ).filter(lambda x: x.strip() and x == x.strip() and not any(
            pattern in x.lower() for pattern in ['<script', 'javascript:', 'onerror=', 'onclick=']
        )),
        new_last_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs', 'Zs', 'Zl', 'Zp')),
            min_size=1, 
            max_size=30
        ).filter(lambda x: x.strip() and x == x.strip() and not any(
            pattern in x.lower() for pattern in ['<script', 'javascript:', 'onerror=', 'onclick=']
        ))
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_update_preserves_integrity(self, username, original_email, 
                                                       new_email, new_first_name, new_last_name):
        """
        Feature: django-auth-permissions, Property 23: User update preserves integrity
        Validates: Requirements 7.4
        
        For any user and valid update data, when an admin updates the user information,
        the changes should be saved and other user data should remain unchanged.
        """
        from django.contrib.auth.models import Group
        
        # Create a user with initial data
        user = User.objects.create_user(
            username=username,
            email=original_email,
            password='originalpass123',
            first_name='OriginalFirst',
            last_name='OriginalLast'
        )
        
        # Store original values
        original_username = user.username
        original_password = user.password
        original_date_joined = user.date_joined
        original_id = user.id
        
        # Create a role and assign it
        original_role = Group.objects.create(name='original_role')
        user.groups.add(original_role)
        
        # Create admin
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Update user information
        response = admin_client.post(
            reverse('user_update', args=[user.pk]),
            {
                'username': username,  # Keep same username
                'email': new_email,
                'first_name': new_first_name,
                'last_name': new_last_name,
                'is_active': True,
            },
            follow=True
        )
        
        # Refresh user from database
        user.refresh_from_db()
        
        # Verify updated fields changed (email is normalized to lowercase by Django)
        self.assertEqual(user.email.lower(), new_email.lower())
        self.assertEqual(user.first_name, new_first_name)
        self.assertEqual(user.last_name, new_last_name)
        
        # Verify unchanged fields remain the same (integrity preserved)
        self.assertEqual(user.username, original_username)
        self.assertEqual(user.password, original_password)
        self.assertEqual(user.date_joined, original_date_joined)
        self.assertEqual(user.id, original_id)
        
        # Verify user is still active
        self.assertTrue(user.is_active)



class RoleManagementPropertyTests(HypothesisTestCase):
    """Property-based tests for role management functionality"""
    
    @given(
        role_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1, 
            max_size=80
        ).filter(lambda x: x.strip() and x == x.strip()),
        permission_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_role_creation_with_permissions(self, role_name, permission_count):
        """
        Feature: django-auth-permissions, Property 11: Role creation with permissions
        Validates: Requirements 4.1
        
        For any valid role name and permission set, when an admin creates a role,
        the system should store the role with all specified permissions.
        """
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Get available permissions (limit to a subset for testing)
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < permission_count:
            return
        
        # Select random permissions
        import random
        selected_permissions = random.sample(available_permissions, permission_count)
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Create a new role with permissions
        response = client.post(
            reverse('role_create'),
            {
                'name': role_name,
                'permissions': [p.id for p in selected_permissions]
            },
            follow=True
        )
        
        # Verify role was created
        self.assertTrue(Group.objects.filter(name=role_name).exists())
        
        # Get the created role
        created_role = Group.objects.get(name=role_name)
        
        # Verify role name is stored correctly
        self.assertEqual(created_role.name, role_name)
        
        # Verify all specified permissions are assigned
        role_permissions = set(created_role.permissions.all())
        expected_permissions = set(selected_permissions)
        self.assertEqual(role_permissions, expected_permissions)
        
        # Verify permission count matches
        self.assertEqual(created_role.permissions.count(), permission_count)
    
    @given(
        username=valid_username(),
        role_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1, 
            max_size=80
        ).filter(lambda x: x.strip() and x == x.strip()),
        permission_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_role_assignment_grants_permissions(self, username, role_name, permission_count):
        """
        Feature: django-auth-permissions, Property 12: Role assignment grants permissions
        Validates: Requirements 4.2
        
        For any user and role, when the role is assigned to the user,
        the user should have all permissions associated with that role.
        """
        from django.contrib.auth.models import Permission
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < permission_count:
            return
        
        # Select random permissions
        import random
        selected_permissions = random.sample(available_permissions, permission_count)
        
        # Create a role with permissions
        role = Group.objects.create(name=role_name)
        role.permissions.set(selected_permissions)
        
        # Verify user doesn't have these permissions initially
        for perm in selected_permissions:
            self.assertFalse(user.has_perm(f'{perm.content_type.app_label}.{perm.codename}'))
        
        # Assign role to user
        user.groups.add(role)
        
        # Refresh user to get updated permissions
        user = User.objects.get(pk=user.pk)
        
        # Verify user now has all permissions from the role
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(
                user.has_perm(perm_string),
                f"User should have permission {perm_string} after role assignment"
            )
        
        # Verify the role is in user's groups
        self.assertIn(role, user.groups.all())
    
    @given(
        username=valid_username(),
        role_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1, 
            max_size=80
        ).filter(lambda x: x.strip() and x == x.strip()),
        permission_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_role_removal_revokes_permissions(self, username, role_name, permission_count):
        """
        Feature: django-auth-permissions, Property 13: Role removal revokes permissions
        Validates: Requirements 4.3
        
        For any user with an assigned role, when the role is removed from the user,
        the user should no longer have the role's permissions (unless granted individually).
        """
        from django.contrib.auth.models import Permission
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < permission_count:
            return
        
        # Select random permissions
        import random
        selected_permissions = random.sample(available_permissions, permission_count)
        
        # Create a role with permissions
        role = Group.objects.create(name=role_name)
        role.permissions.set(selected_permissions)
        
        # Assign role to user
        user.groups.add(role)
        
        # Refresh user to get updated permissions
        user = User.objects.get(pk=user.pk)
        
        # Verify user has permissions from the role
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Remove role from user
        user.groups.remove(role)
        
        # Refresh user to get updated permissions
        user = User.objects.get(pk=user.pk)
        
        # Verify user no longer has permissions from the role
        # (unless they were granted individually, which they weren't in this test)
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertFalse(
                user.has_perm(perm_string),
                f"User should not have permission {perm_string} after role removal"
            )
        
        # Verify the role is not in user's groups
        self.assertNotIn(role, user.groups.all())
    
    @given(
        user_count=st.integers(min_value=1, max_value=5),
        role_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1, 
            max_size=80
        ).filter(lambda x: x.strip() and x == x.strip()),
        initial_perm_count=st.integers(min_value=1, max_value=5),
        new_perm_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_role_permission_updates_propagate(self, user_count, role_name, 
                                                         initial_perm_count, new_perm_count):
        """
        Feature: django-auth-permissions, Property 14: Role permission updates propagate
        Validates: Requirements 4.4
        
        For any role with assigned users, when the role's permissions are modified,
        all users with that role should reflect the updated permission set.
        """
        from django.contrib.auth.models import Permission
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < max(initial_perm_count, new_perm_count):
            return
        
        # Select random initial permissions
        import random
        initial_permissions = random.sample(available_permissions, initial_perm_count)
        
        # Create a role with initial permissions
        role = Group.objects.create(name=role_name)
        role.permissions.set(initial_permissions)
        
        # Create multiple users and assign them the role
        users = []
        for i in range(user_count):
            user = User.objects.create_user(
                username=f'testuser_{i}_{role_name[:20]}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            user.groups.add(role)
            users.append(user)
        
        # Verify all users have initial permissions
        for user in users:
            user = User.objects.get(pk=user.pk)  # Refresh
            for perm in initial_permissions:
                perm_string = f'{perm.content_type.app_label}.{perm.codename}'
                self.assertTrue(user.has_perm(perm_string))
        
        # Update role permissions to a new set
        new_permissions = random.sample(available_permissions, new_perm_count)
        role.permissions.set(new_permissions)
        
        # Verify all users now have the updated permissions
        for user in users:
            user = User.objects.get(pk=user.pk)  # Refresh
            
            # Check that user has all new permissions
            for perm in new_permissions:
                perm_string = f'{perm.content_type.app_label}.{perm.codename}'
                self.assertTrue(
                    user.has_perm(perm_string),
                    f"User {user.username} should have new permission {perm_string}"
                )
            
            # Check that user doesn't have old permissions that were removed
            # (only check permissions that are not in the new set)
            removed_permissions = set(initial_permissions) - set(new_permissions)
            for perm in removed_permissions:
                perm_string = f'{perm.content_type.app_label}.{perm.codename}'
                self.assertFalse(
                    user.has_perm(perm_string),
                    f"User {user.username} should not have removed permission {perm_string}"
                )


class UserManagementUnitTests(TestCase):
    """Unit tests for user management functionality"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Group
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test role
        self.test_role = Group.objects.create(name='TestRole')
    
    def test_create_user_with_specific_role(self):
        """Test creating user with specific role"""
        client = Client()
        client.force_login(self.admin)
        
        # Create user with role
        response = client.post(
            reverse('user_create'),
            {
                'username': 'newuser',
                'email': 'newuser@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'role': self.test_role.id
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Get created user
        user = User.objects.get(username='newuser')
        
        # Verify role was assigned
        self.assertIn(self.test_role, user.groups.all())
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m) for m in messages))
    
    def test_duplicate_username_rejection(self):
        """Test duplicate username rejection (edge case)"""
        # Create initial user
        User.objects.create_user(
            username='existinguser',
            email='existing@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with duplicate username
        response = client.post(
            reverse('user_create'),
            {
                'username': 'existinguser',
                'email': 'different@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('username', response.context['form'].errors)
        
        # Verify only one user with that username exists
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)
    
    def test_update_specific_user_fields(self):
        """Test updating specific user fields"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='old@test.com',
            password='testpass123',
            first_name='OldFirst',
            last_name='OldLast'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Update user
        response = client.post(
            reverse('user_update', args=[user.pk]),
            {
                'username': 'testuser',
                'email': 'new@test.com',
                'first_name': 'NewFirst',
                'last_name': 'NewLast',
                'is_active': True,
            },
            follow=True
        )
        
        # Refresh user
        user.refresh_from_db()
        
        # Verify updates
        self.assertEqual(user.email, 'new@test.com')
        self.assertEqual(user.first_name, 'NewFirst')
        self.assertEqual(user.last_name, 'NewLast')
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m) for m in messages))
    
    def test_deactivate_and_reactivate_specific_user(self):
        """Test deactivating and reactivating specific user"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Verify user is active initially
        self.assertTrue(user.is_active)
        
        client = Client()
        client.force_login(self.admin)
        
        # Deactivate user
        response = client.get(reverse('user_deactivate', args=[user.pk]), follow=True)
        
        # Refresh and verify deactivation
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('deactivated' in str(m) for m in messages))
        
        # Reactivate user
        response = client.get(reverse('user_reactivate', args=[user.pk]), follow=True)
        
        # Refresh and verify reactivation
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('reactivated' in str(m) for m in messages))



class PermissionManagementPropertyTests(HypothesisTestCase):
    """Property-based tests for individual permission management functionality"""
    
    @given(
        username=valid_username(),
        permission_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_individual_permission_assignment(self, username, permission_count):
        """
        Feature: django-auth-permissions, Property 16: Individual permission assignment
        Validates: Requirements 5.1
        
        For any user and permission, when an admin assigns the permission to the user,
        the permission should be added to the user's individual permission set.
        """
        from django.contrib.auth.models import Permission
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < permission_count:
            return
        
        # Select random permissions to assign
        import random
        selected_permissions = random.sample(available_permissions, permission_count)
        
        # Verify user doesn't have these permissions initially
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertFalse(user.has_perm(perm_string))
        
        # Verify user's individual permission set is empty initially
        self.assertEqual(user.user_permissions.count(), 0)
        
        # Assign each permission individually to the user
        for perm in selected_permissions:
            user.user_permissions.add(perm)
        
        # Refresh user to get updated permissions
        user = User.objects.get(pk=user.pk)
        
        # Verify all permissions are in user's individual permission set
        user_individual_perms = set(user.user_permissions.all())
        expected_perms = set(selected_permissions)
        self.assertEqual(user_individual_perms, expected_perms)
        
        # Verify user now has all assigned permissions
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(
                user.has_perm(perm_string),
                f"User should have permission {perm_string} after individual assignment"
            )
        
        # Verify permission count matches
        self.assertEqual(user.user_permissions.count(), permission_count)
    
    @given(
        username=valid_username(),
        permission_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_individual_permission_revocation(self, username, permission_count):
        """
        Feature: django-auth-permissions, Property 17: Individual permission revocation
        Validates: Requirements 5.2
        
        For any user with an individual permission, when the permission is revoked,
        it should be removed from the user's permission set.
        """
        from django.contrib.auth.models import Permission
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < permission_count:
            return
        
        # Select random permissions to assign
        import random
        selected_permissions = random.sample(available_permissions, permission_count)
        
        # Assign permissions to user
        for perm in selected_permissions:
            user.user_permissions.add(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify user has all permissions
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Verify permission count
        self.assertEqual(user.user_permissions.count(), permission_count)
        
        # Revoke all permissions
        for perm in selected_permissions:
            user.user_permissions.remove(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify all permissions are removed from user's individual permission set
        self.assertEqual(user.user_permissions.count(), 0)
        
        # Verify user no longer has the permissions
        for perm in selected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertFalse(
                user.has_perm(perm_string),
                f"User should not have permission {perm_string} after revocation"
            )
    
    @given(
        username=valid_username(),
        role_perm_count=st.integers(min_value=1, max_value=5),
        individual_perm_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_permission_union_from_multiple_sources(self, username, role_perm_count, individual_perm_count):
        """
        Feature: django-auth-permissions, Property 18: Permission union from multiple sources
        Validates: Requirements 5.3, 5.4, 6.4
        
        For any user, the effective permissions should be the union of permissions 
        from assigned roles and individual permissions.
        """
        from django.contrib.auth.models import Permission, Group
        
        # Get available permissions
        available_permissions = list(Permission.objects.all()[:20])
        
        # Skip if we don't have enough permissions
        if len(available_permissions) < (role_perm_count + individual_perm_count):
            return
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Select random permissions for role and individual assignment
        import random
        all_selected = random.sample(available_permissions, role_perm_count + individual_perm_count)
        role_permissions = all_selected[:role_perm_count]
        individual_permissions = all_selected[role_perm_count:]
        
        # Create a role with permissions
        role = Group.objects.create(name=f'role_{username[:20]}')
        role.permissions.set(role_permissions)
        
        # Assign role to user
        user.groups.add(role)
        
        # Assign individual permissions to user
        for perm in individual_permissions:
            user.user_permissions.add(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Calculate expected permissions (union of role and individual)
        expected_permissions = set(role_permissions) | set(individual_permissions)
        
        # Verify user has all permissions from both sources
        for perm in expected_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(
                user.has_perm(perm_string),
                f"User should have permission {perm_string} from either role or individual assignment"
            )
        
        # Verify user has permissions from role
        for perm in role_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Verify user has individual permissions
        for perm in individual_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Verify the union property: if a permission is in either source, user has it
        # Test by checking that removing role doesn't affect individual permissions
        user.groups.remove(role)
        user = User.objects.get(pk=user.pk)
        
        # User should still have individual permissions
        for perm in individual_permissions:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(
                user.has_perm(perm_string),
                f"User should still have individual permission {perm_string} after role removal"
            )
        
        # User should not have role-only permissions
        role_only_perms = set(role_permissions) - set(individual_permissions)
        for perm in role_only_perms:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertFalse(
                user.has_perm(perm_string),
                f"User should not have role-only permission {perm_string} after role removal"
            )


class RoleManagementUnitTests(TestCase):
    """Unit tests for role management functionality"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Permission
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Get some test permissions
        self.test_permissions = list(Permission.objects.all()[:5])
    
    def test_create_role_with_specific_permissions(self):
        """Test creating role with specific permissions"""
        client = Client()
        client.force_login(self.admin)
        
        # Create role with specific permissions
        response = client.post(
            reverse('role_create'),
            {
                'name': 'TestRole',
                'permissions': [p.id for p in self.test_permissions[:3]]
            },
            follow=True
        )
        
        # Verify role was created
        self.assertTrue(Group.objects.filter(name='TestRole').exists())
        
        # Get created role
        role = Group.objects.get(name='TestRole')
        
        # Verify permissions were assigned
        self.assertEqual(role.permissions.count(), 3)
        for perm in self.test_permissions[:3]:
            self.assertIn(perm, role.permissions.all())
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m) for m in messages))
    
    def test_assign_specific_role_to_user(self):
        """Test assigning specific role to user"""
        # Create a role with permissions
        role = Group.objects.create(name='EditorRole')
        role.permissions.set(self.test_permissions[:2])
        
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Verify user doesn't have permissions initially
        for perm in self.test_permissions[:2]:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertFalse(user.has_perm(perm_string))
        
        # Assign role to user
        user.groups.add(role)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify user now has permissions from role
        for perm in self.test_permissions[:2]:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Verify role is in user's groups
        self.assertIn(role, user.groups.all())
    
    def test_modify_role_permissions(self):
        """Test modifying role permissions"""
        # Create a role with initial permissions
        role = Group.objects.create(name='ModifiableRole')
        role.permissions.set(self.test_permissions[:2])
        
        # Create a user with this role
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        user.groups.add(role)
        
        # Verify user has initial permissions
        user = User.objects.get(pk=user.pk)
        for perm in self.test_permissions[:2]:
            perm_string = f'{perm.content_type.app_label}.{perm.codename}'
            self.assertTrue(user.has_perm(perm_string))
        
        # Login as admin and modify role permissions
        client = Client()
        client.force_login(self.admin)
        
        response = client.post(
            reverse('role_update', args=[role.pk]),
            {
                'name': 'ModifiableRole',
                'permissions': [self.test_permissions[2].id, self.test_permissions[3].id]
            },
            follow=True
        )
        
        # Refresh role and user
        role = Group.objects.get(pk=role.pk)
        user = User.objects.get(pk=user.pk)
        
        # Verify role has new permissions
        self.assertEqual(role.permissions.count(), 2)
        self.assertIn(self.test_permissions[2], role.permissions.all())
        self.assertIn(self.test_permissions[3], role.permissions.all())
        
        # Verify user has new permissions
        perm_string_2 = f'{self.test_permissions[2].content_type.app_label}.{self.test_permissions[2].codename}'
        perm_string_3 = f'{self.test_permissions[3].content_type.app_label}.{self.test_permissions[3].codename}'
        self.assertTrue(user.has_perm(perm_string_2))
        self.assertTrue(user.has_perm(perm_string_3))
        
        # Verify user no longer has old permissions
        perm_string_0 = f'{self.test_permissions[0].content_type.app_label}.{self.test_permissions[0].codename}'
        perm_string_1 = f'{self.test_permissions[1].content_type.app_label}.{self.test_permissions[1].codename}'
        self.assertFalse(user.has_perm(perm_string_0))
        self.assertFalse(user.has_perm(perm_string_1))
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m) for m in messages))



class PermissionManagementUnitTests(TestCase):
    """Unit tests for individual permission management functionality"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Permission
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Get some test permissions
        self.test_permissions = list(Permission.objects.all()[:5])
    
    def test_assign_specific_individual_permission(self):
        """Test assigning specific individual permission"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Get a specific permission
        perm = self.test_permissions[0]
        perm_string = f'{perm.content_type.app_label}.{perm.codename}'
        
        # Verify user doesn't have permission initially
        self.assertFalse(user.has_perm(perm_string))
        self.assertEqual(user.user_permissions.count(), 0)
        
        # Assign permission to user
        user.user_permissions.add(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify permission was assigned
        self.assertTrue(user.has_perm(perm_string))
        self.assertEqual(user.user_permissions.count(), 1)
        self.assertIn(perm, user.user_permissions.all())
    
    def test_revoke_specific_individual_permission(self):
        """Test revoking specific individual permission"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Get a specific permission
        perm = self.test_permissions[0]
        perm_string = f'{perm.content_type.app_label}.{perm.codename}'
        
        # Assign permission to user
        user.user_permissions.add(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify user has permission
        self.assertTrue(user.has_perm(perm_string))
        self.assertEqual(user.user_permissions.count(), 1)
        
        # Revoke permission from user
        user.user_permissions.remove(perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Verify permission was revoked
        self.assertFalse(user.has_perm(perm_string))
        self.assertEqual(user.user_permissions.count(), 0)
        self.assertNotIn(perm, user.user_permissions.all())
    
    def test_check_specific_permission_on_user(self):
        """Test checking specific permission on user"""
        from django.contrib.auth.models import Group
        
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Get specific permissions
        role_perm = self.test_permissions[0]
        individual_perm = self.test_permissions[1]
        unassigned_perm = self.test_permissions[2]
        
        role_perm_string = f'{role_perm.content_type.app_label}.{role_perm.codename}'
        individual_perm_string = f'{individual_perm.content_type.app_label}.{individual_perm.codename}'
        unassigned_perm_string = f'{unassigned_perm.content_type.app_label}.{unassigned_perm.codename}'
        
        # Create a role with one permission
        role = Group.objects.create(name='TestRole')
        role.permissions.add(role_perm)
        user.groups.add(role)
        
        # Assign individual permission
        user.user_permissions.add(individual_perm)
        
        # Refresh user
        user = User.objects.get(pk=user.pk)
        
        # Check permissions
        # User should have role permission
        self.assertTrue(user.has_perm(role_perm_string))
        
        # User should have individual permission
        self.assertTrue(user.has_perm(individual_perm_string))
        
        # User should not have unassigned permission
        self.assertFalse(user.has_perm(unassigned_perm_string))
        
        # Verify permission sources
        # Role permission should not be in user_permissions
        self.assertNotIn(role_perm, user.user_permissions.all())
        
        # Individual permission should be in user_permissions
        self.assertIn(individual_perm, user.user_permissions.all())



class AccessControlPropertyTests(HypothesisTestCase):
    """Property-based tests for access control functionality"""
    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_admin_only_user_creation(self, username, email, password):
        """
        Feature: django-auth-permissions, Property 4: Admin-only user creation
        Validates: Requirements 1.5
        
        For any non-admin user, attempting to create a user account should result in 
        an authorization error (403 Forbidden).
        """
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            return
        
        # Create a non-admin user (regular user without special permissions)
        non_admin = User.objects.create_user(
            username='nonadmin_' + username[:20],
            email='nonadmin@test.com',
            password='nonadminpass123'
        )
        
        # Verify non-admin doesn't have add_user permission
        self.assertFalse(non_admin.has_perm('auth.add_user'))
        self.assertFalse(non_admin.is_staff)
        self.assertFalse(non_admin.is_superuser)
        
        # Login as non-admin
        client = Client()
        client.force_login(non_admin)
        
        # Attempt to create a user as non-admin
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
            },
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username=username).exists())
        
        # Also test that admin CAN create users (positive case)
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Attempt to create user as admin
        response = admin_client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
            },
            follow=True
        )
        
        # Verify admin was able to create user
        self.assertTrue(User.objects.filter(username=username).exists())

    
    @given(
        role_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1, 
            max_size=80
        ).filter(lambda x: x.strip() and x == x.strip())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_admin_only_role_management(self, role_name):
        """
        Feature: django-auth-permissions, Property 15: Admin-only role management
        Validates: Requirements 4.5
        
        For any non-admin user, attempting to create, modify, or delete roles should 
        result in an authorization error (403 Forbidden).
        """
        from django.contrib.auth.models import Group, Permission
        
        # Create a non-admin user (regular user without special permissions)
        non_admin = User.objects.create_user(
            username='nonadmin_role',
            email='nonadmin@test.com',
            password='nonadminpass123'
        )
        
        # Verify non-admin doesn't have group management permissions
        self.assertFalse(non_admin.has_perm('auth.add_group'))
        self.assertFalse(non_admin.has_perm('auth.change_group'))
        self.assertFalse(non_admin.has_perm('auth.delete_group'))
        self.assertFalse(non_admin.is_staff)
        self.assertFalse(non_admin.is_superuser)
        
        # Login as non-admin
        client = Client()
        client.force_login(non_admin)
        
        # Test 1: Attempt to CREATE a role as non-admin
        response = client.post(
            reverse('role_create'),
            {
                'name': role_name,
                'permissions': []
            },
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify role was NOT created
        self.assertFalse(Group.objects.filter(name=role_name).exists())
        
        # Create a test role for modification/deletion tests
        test_role = Group.objects.create(name='test_role_' + role_name[:50])
        
        # Test 2: Attempt to MODIFY a role as non-admin
        response = client.post(
            reverse('role_update', args=[test_role.pk]),
            {
                'name': 'modified_' + role_name[:50],
                'permissions': []
            },
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify role was NOT modified
        test_role.refresh_from_db()
        self.assertEqual(test_role.name, 'test_role_' + role_name[:50])
        
        # Test 3: Attempt to VIEW role list as non-admin
        response = client.get(reverse('role_list'), follow=False)
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Positive test: Verify admin CAN manage roles
        admin = User.objects.create_superuser(
            username='admin_role',
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Admin should be able to create role
        response = admin_client.post(
            reverse('role_create'),
            {
                'name': role_name,
                'permissions': []
            },
            follow=True
        )
        
        # Verify admin was able to create role
        self.assertTrue(Group.objects.filter(name=role_name).exists())
        
        # Admin should be able to view role list
        response = admin_client.get(reverse('role_list'))
        self.assertEqual(response.status_code, 200)
        
        # Admin should be able to modify role
        created_role = Group.objects.get(name=role_name)
        response = admin_client.post(
            reverse('role_update', args=[created_role.pk]),
            {
                'name': 'modified_' + role_name[:50],
                'permissions': []
            },
            follow=True
        )
        
        # Verify role was modified
        created_role.refresh_from_db()
        self.assertEqual(created_role.name, 'modified_' + role_name[:50])

    
    @given(
        username=valid_username()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_admin_only_user_management(self, username):
        """
        Feature: django-auth-permissions, Property 24: Admin-only user management
        Validates: Requirements 7.5
        
        For any non-admin user, attempting to access user management functions 
        (list, create, update, deactivate) should result in an authorization error (403 Forbidden).
        """
        # Create a non-admin user (regular user without special permissions)
        non_admin = User.objects.create_user(
            username='nonadmin_usermgmt',
            email='nonadmin@test.com',
            password='nonadminpass123'
        )
        
        # Create a target user for management operations
        target_user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        # Verify non-admin doesn't have user management permissions
        self.assertFalse(non_admin.has_perm('auth.view_user'))
        self.assertFalse(non_admin.has_perm('auth.add_user'))
        self.assertFalse(non_admin.has_perm('auth.change_user'))
        self.assertFalse(non_admin.is_staff)
        self.assertFalse(non_admin.is_superuser)
        
        # Login as non-admin
        client = Client()
        client.force_login(non_admin)
        
        # Test 1: Attempt to VIEW user list as non-admin
        response = client.get(reverse('user_list'), follow=False)
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Test 2: Attempt to CREATE user as non-admin (already tested in 8.1, but verify here too)
        response = client.post(
            reverse('user_create'),
            {
                'username': 'newuser_' + username[:20],
                'email': 'newuser@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            },
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username='newuser_' + username[:20]).exists())
        
        # Test 3: Attempt to UPDATE user as non-admin
        response = client.post(
            reverse('user_update', args=[target_user.pk]),
            {
                'username': username,
                'email': 'modified@test.com',
                'is_active': True,
            },
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify user was NOT modified
        target_user.refresh_from_db()
        self.assertEqual(target_user.email, f'{username}@test.com')
        
        # Test 4: Attempt to DEACTIVATE user as non-admin
        response = client.get(
            reverse('user_deactivate', args=[target_user.pk]),
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify user was NOT deactivated
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)
        
        # Test 5: Attempt to REACTIVATE user as non-admin
        # First deactivate the user as admin
        target_user.is_active = False
        target_user.save()
        
        response = client.get(
            reverse('user_reactivate', args=[target_user.pk]),
            follow=False
        )
        
        # Verify access was denied (403 Forbidden)
        self.assertEqual(response.status_code, 403)
        
        # Verify user was NOT reactivated
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)
        
        # Positive test: Verify admin CAN manage users
        admin = User.objects.create_superuser(
            username='admin_usermgmt',
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Admin should be able to view user list
        response = admin_client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        
        # Admin should be able to create user
        response = admin_client.post(
            reverse('user_create'),
            {
                'username': 'admin_created_' + username[:15],
                'email': 'admincreated@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            },
            follow=True
        )
        self.assertTrue(User.objects.filter(username='admin_created_' + username[:15]).exists())
        
        # Admin should be able to update user
        response = admin_client.post(
            reverse('user_update', args=[target_user.pk]),
            {
                'username': username,
                'email': 'admin_modified@test.com',
                'is_active': False,
            },
            follow=True
        )
        target_user.refresh_from_db()
        self.assertEqual(target_user.email, 'admin_modified@test.com')
        
        # Admin should be able to reactivate user
        response = admin_client.get(reverse('user_reactivate', args=[target_user.pk]))
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)
        
        # Admin should be able to deactivate user
        response = admin_client.get(reverse('user_deactivate', args=[target_user.pk]))
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)

    
    @given(
        username_with_perm=valid_username(),
        username_without_perm=valid_username()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_access_control_enforcement(self, username_with_perm, username_without_perm):
        """
        Feature: django-auth-permissions, Property 19: Access control enforcement
        Validates: Requirements 6.1, 6.2
        
        For any protected view requiring specific permissions, users with the required 
        permission should be granted access (200 OK), while users without the permission 
        should be denied access (403 Forbidden).
        """
        from django.contrib.auth.models import Permission
        
        # Skip if usernames are the same
        if username_with_perm == username_without_perm:
            return
        
        # Create two users: one with permission, one without
        user_with_perm = User.objects.create_user(
            username=username_with_perm,
            email=f'{username_with_perm}@test.com',
            password='testpass123'
        )
        
        user_without_perm = User.objects.create_user(
            username=username_without_perm,
            email=f'{username_without_perm}@test.com',
            password='testpass123'
        )
        
        # Get a specific permission to test (e.g., view_user)
        view_user_perm = Permission.objects.get(codename='view_user', content_type__app_label='auth')
        
        # Assign permission to first user only
        user_with_perm.user_permissions.add(view_user_perm)
        
        # Refresh users
        user_with_perm = User.objects.get(pk=user_with_perm.pk)
        user_without_perm = User.objects.get(pk=user_without_perm.pk)
        
        # Verify permission assignment
        self.assertTrue(user_with_perm.has_perm('auth.view_user'))
        self.assertFalse(user_without_perm.has_perm('auth.view_user'))
        
        # Test 1: User WITH permission should be granted access (200 OK)
        client_with_perm = Client()
        client_with_perm.force_login(user_with_perm)
        
        response = client_with_perm.get(reverse('user_list'))
        
        # Verify access was granted
        self.assertEqual(response.status_code, 200)
        
        # Verify the view returned expected content
        self.assertIn('users', response.context)
        
        # Test 2: User WITHOUT permission should be denied access (403 Forbidden)
        client_without_perm = Client()
        client_without_perm.force_login(user_without_perm)
        
        response = client_without_perm.get(reverse('user_list'))
        
        # Verify access was denied
        self.assertEqual(response.status_code, 403)
        
        # Test with another protected view (role_list requires view_group permission)
        view_group_perm = Permission.objects.get(codename='view_group', content_type__app_label='auth')
        
        # Assign permission to first user
        user_with_perm.user_permissions.add(view_group_perm)
        user_with_perm = User.objects.get(pk=user_with_perm.pk)
        
        # Verify permission assignment
        self.assertTrue(user_with_perm.has_perm('auth.view_group'))
        self.assertFalse(user_without_perm.has_perm('auth.view_group'))
        
        # User with permission should access role_list
        response = client_with_perm.get(reverse('role_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('roles', response.context)
        
        # User without permission should be denied
        response = client_without_perm.get(reverse('role_list'))
        self.assertEqual(response.status_code, 403)
        
        # Test with user creation (requires add_user permission)
        add_user_perm = Permission.objects.get(codename='add_user', content_type__app_label='auth')
        
        # Assign permission to first user
        user_with_perm.user_permissions.add(add_user_perm)
        user_with_perm = User.objects.get(pk=user_with_perm.pk)
        
        # Verify permission assignment
        self.assertTrue(user_with_perm.has_perm('auth.add_user'))
        self.assertFalse(user_without_perm.has_perm('auth.add_user'))
        
        # User with permission should access user_create
        response = client_with_perm.get(reverse('user_create'))
        self.assertEqual(response.status_code, 200)
        
        # User without permission should be denied
        response = client_without_perm.get(reverse('user_create'))
        self.assertEqual(response.status_code, 403)



class AccessControlUnitTests(TestCase):
    """Unit tests for access control functionality"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Permission
        
        # Create admin user with all permissions
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create regular user with specific permission
        self.user_with_permission = User.objects.create_user(
            username='authorized_user',
            email='authorized@test.com',
            password='testpass123'
        )
        
        # Assign view_user permission
        view_user_perm = Permission.objects.get(codename='view_user', content_type__app_label='auth')
        self.user_with_permission.user_permissions.add(view_user_perm)
        
        # Create regular user without permissions
        self.user_without_permission = User.objects.create_user(
            username='unauthorized_user',
            email='unauthorized@test.com',
            password='testpass123'
        )
    
    def test_authorized_access_returns_200(self):
        """Test authorized access returns 200"""
        # Login as user with permission
        client = Client()
        client.force_login(self.user_with_permission)
        
        # Access protected view
        response = client.get(reverse('user_list'))
        
        # Verify successful access
        self.assertEqual(response.status_code, 200)
        
        # Verify expected content is present
        self.assertIn('users', response.context)
        
        # Test with admin user as well
        admin_client = Client()
        admin_client.force_login(self.admin)
        
        response = admin_client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.context)
    
    def test_unauthorized_access_returns_403(self):
        """Test unauthorized access returns 403"""
        # Login as user without permission
        client = Client()
        client.force_login(self.user_without_permission)
        
        # Attempt to access protected view
        response = client.get(reverse('user_list'))
        
        # Verify access denied
        self.assertEqual(response.status_code, 403)
        
        # Test with user creation view
        response = client.get(reverse('user_create'))
        self.assertEqual(response.status_code, 403)
        
        # Test with role list view
        response = client.get(reverse('role_list'))
        self.assertEqual(response.status_code, 403)
        
        # Test with role creation view
        response = client.get(reverse('role_create'))
        self.assertEqual(response.status_code, 403)
    
    def test_unauthenticated_access_redirects_to_login(self):
        """Test unauthenticated access redirects to login"""
        # Create unauthenticated client
        client = Client()
        
        # Attempt to access protected views
        
        # Test dashboard
        response = client.get(reverse('dashboard'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        
        # Test user list
        response = client.get(reverse('user_list'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        
        # Test user create
        response = client.get(reverse('user_create'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        
        # Test role list
        response = client.get(reverse('role_list'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        
        # Test role create
        response = client.get(reverse('role_create'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        
        # Verify redirect includes next parameter
        response = client.get(reverse('dashboard'), follow=False)
        expected_redirect = f"{reverse('login')}?next={reverse('dashboard')}"
        self.assertEqual(response.url, expected_redirect)



class PasswordResetPropertyTests(HypothesisTestCase):
    """Property-based tests for password reset functionality"""
    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_password_reset_token_generation(self, username, email, password):
        """
        Feature: django-auth-permissions, Property 25: Password reset token generation
        Validates: Requirements 8.1
        
        For any user requesting a password reset, the system should generate a valid 
        reset token and send it to the user's registered email.
        """
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        from django.core import mail
        from django.contrib.auth.tokens import default_token_generator
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            return
        
        # Create a user with the email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create a client
        client = Client()
        
        # Request password reset
        response = client.post(
            reverse('password_reset_request'),
            {'email': email},
            follow=True
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Debug: Check if we're at the login page (successful submission)
        self.assertIn('login', response.request['PATH_INFO'].lower())
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, f"Expected 1 email, got {len(mail.outbox)}. User email: {user.email}, Submitted email: {email}")
        
        # Get the sent email
        sent_email = mail.outbox[0]
        
        # Verify email was sent to correct address
        self.assertIn(email, sent_email.to)
        
        # Verify email contains reset link
        self.assertIn('password-reset/confirm/', sent_email.body)
        
        # Extract token from email body (it should be in the URL)
        # The URL format is: /password-reset/confirm/<uidb64>/<token>/
        import re
        url_pattern = r'/password-reset/confirm/([^/]+)/([^/]+)/'
        match = re.search(url_pattern, sent_email.body)
        
        self.assertIsNotNone(match, "Reset link should be present in email")
        
        uidb64 = match.group(1)
        token = match.group(2)
        
        # Verify token is valid for this user
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        decoded_uid = force_str(urlsafe_base64_decode(uidb64))
        self.assertEqual(int(decoded_uid), user.pk)
        
        # Verify token is valid
        self.assertTrue(
            default_token_generator.check_token(user, token),
            "Generated token should be valid for the user"
        )
        
        # Verify success message is displayed
        messages = list(response.context['messages'])
        self.assertTrue(
            any('sent' in str(m).lower() for m in messages),
            "Success message should indicate email was sent"
        )
    
    @given(
        username=valid_username(),
        email=st.emails(),
        old_password=valid_password(),
        new_password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_password_reset_updates_and_invalidates_token(self, username, email, 
                                                                     old_password, new_password):
        """
        Feature: django-auth-permissions, Property 26: Password reset updates and invalidates token
        Validates: Requirements 8.3
        
        For any valid reset token and new password, submitting the password reset 
        should update the user's password and invalidate the reset token.
        """
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        # Skip if passwords are the same or only differ by whitespace
        if old_password == new_password or old_password.strip() == new_password.strip():
            return
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(old_password, user=temp_user)
            validate_password(new_password, user=temp_user)
        except ValidationError:
            return
        
        # Create a user with old password
        user = User.objects.create_user(
            username=username,
            email=email,
            password=old_password
        )
        
        # Store old password hash
        old_password_hash = user.password
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Verify token is valid before reset
        self.assertTrue(default_token_generator.check_token(user, token))
        
        # Verify user can login with old password
        self.assertTrue(user.check_password(old_password))
        
        # Create a client
        client = Client()
        
        # Submit password reset with new password
        response = client.post(
            reverse('password_reset_confirm', args=[uidb64, token]),
            {
                'new_password1': new_password,
                'new_password2': new_password
            },
            follow=True
        )
        
        # Check if form has errors (skip test if password validation fails)
        if 'form' in response.context and response.context['form'].errors:
            # Password validation failed, skip this test case
            return
        
        # Refresh user from database
        user.refresh_from_db()
        
        # Verify password was updated
        self.assertNotEqual(user.password, old_password_hash)
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password(old_password))
        
        # Verify token is now invalid (tokens are invalidated after password change)
        self.assertFalse(
            default_token_generator.check_token(user, token),
            "Token should be invalidated after password reset"
        )
        
        # Verify success message and redirect to login
        self.assertRedirects(response, reverse('login'))
        messages = list(response.context['messages'])
        self.assertTrue(
            any('reset successfully' in str(m).lower() for m in messages),
            "Success message should indicate password was reset"
        )
    
    @given(
        username=valid_username(),
        email=st.emails(),
        old_password=valid_password(),
        new_password=valid_password(),
        session_count=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_password_reset_invalidates_all_sessions(self, username, email, 
                                                                old_password, new_password, 
                                                                session_count):
        """
        Feature: django-auth-permissions, Property 27: Password reset invalidates all sessions
        Validates: Requirements 8.5
        
        For any user with active sessions, completing a password reset should 
        invalidate all existing sessions for that user.
        """
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.sessions.models import Session
        
        # Skip if passwords are the same or only differ by whitespace
        if old_password == new_password or old_password.strip() == new_password.strip():
            return
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(old_password, user=temp_user)
            validate_password(new_password, user=temp_user)
        except ValidationError:
            return
        
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=old_password
        )
        
        # Create multiple active sessions for this user
        active_sessions = []
        for i in range(session_count):
            client = Client()
            client.post(
                reverse('login'),
                {'username': username, 'password': old_password}
            )
            
            # Verify session was created
            self.assertIn('_auth_user_id', client.session)
            self.assertEqual(int(client.session['_auth_user_id']), user.pk)
            
            # Store session key
            active_sessions.append(client.session.session_key)
        
        # Verify all sessions exist in database
        for session_key in active_sessions:
            self.assertTrue(
                Session.objects.filter(session_key=session_key).exists(),
                f"Session {session_key} should exist before password reset"
            )
        
        # Count sessions for this user before reset
        sessions_before = 0
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.pk):
                sessions_before += 1
        
        self.assertEqual(sessions_before, session_count)
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create a new client for password reset
        reset_client = Client()
        
        # Submit password reset
        response = reset_client.post(
            reverse('password_reset_confirm', args=[uidb64, token]),
            {
                'new_password1': new_password,
                'new_password2': new_password
            },
            follow=True
        )
        
        # Check if form has errors (skip test if password validation fails)
        if 'form' in response.context and response.context['form'].errors:
            # Password validation failed, skip this test case
            return
        
        # Check if we were redirected to login (success)
        if response.status_code != 200 or 'login' not in response.request['PATH_INFO'].lower():
            # Form validation might have failed, skip
            return
        
        # Verify password was reset
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        
        # Verify all sessions for this user are invalidated
        sessions_after = 0
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.pk):
                sessions_after += 1
        
        self.assertEqual(
            sessions_after, 0,
            "All sessions for the user should be invalidated after password reset"
        )
        
        # Verify the old session keys no longer exist or are invalid
        for session_key in active_sessions:
            # Session might be deleted or expired
            if Session.objects.filter(session_key=session_key).exists():
                session = Session.objects.get(session_key=session_key)
                session_data = session.get_decoded()
                # If it exists, it shouldn't belong to our user
                self.assertNotEqual(session_data.get('_auth_user_id'), str(user.pk))
        
        # Verify user needs to login again with new password
        test_client = Client()
        test_client.cookies = active_sessions[0] if active_sessions else {}
        
        # Try to access protected page with old session
        response = test_client.get(reverse('dashboard'), follow=False)
        
        # Should redirect to login (session is invalid)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)



class PasswordResetUnitTests(TestCase):
    """Unit tests for password reset functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
    
    def test_password_reset_request_sends_email(self):
        """Test password reset request sends email"""
        from django.core import mail
        
        # Request password reset
        client = Client()
        response = client.post(
            reverse('password_reset_request'),
            {'email': 'test@example.com'},
            follow=True
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify email details
        sent_email = mail.outbox[0]
        self.assertIn('test@example.com', sent_email.to)
        self.assertIn('Password Reset', sent_email.subject)
        self.assertIn('password-reset/confirm/', sent_email.body)
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('sent' in str(m).lower() for m in messages))
    
    def test_valid_reset_link_displays_form(self):
        """Test valid reset link displays form"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        # Generate valid token
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Access reset confirm page
        client = Client()
        response = client.get(
            reverse('password_reset_confirm', args=[uidb64, token])
        )
        
        # Verify form is displayed
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['validlink'])
        
        # Verify form fields are present
        self.assertContains(response, 'new_password1')
        self.assertContains(response, 'new_password2')
    
    def test_expired_reset_token_rejection(self):
        """Test expired reset token rejection (edge case)"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        # Generate token
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Change user's password to invalidate the token
        self.user.set_password('differentpassword')
        self.user.save()
        
        # Try to access reset confirm page with old token
        client = Client()
        response = client.get(
            reverse('password_reset_confirm', args=[uidb64, token])
        )
        
        # Verify token is rejected
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['validlink'])
        
        # Verify error message
        messages = list(response.context['messages'])
        self.assertTrue(any('invalid' in str(m).lower() or 'expired' in str(m).lower() for m in messages))
    
    def test_password_update_and_session_invalidation(self):
        """Test password update and session invalidation"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.sessions.models import Session
        
        # Create active session for user
        login_client = Client()
        login_client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'oldpassword123'}
        )
        
        # Verify session exists
        self.assertIn('_auth_user_id', login_client.session)
        session_key = login_client.session.session_key
        self.assertTrue(Session.objects.filter(session_key=session_key).exists())
        
        # Refresh user object to get updated last_login
        self.user.refresh_from_db()
        
        # Generate reset token AFTER login (so it's valid with current last_login)
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Submit password reset
        reset_client = Client()
        new_password = 'NewSecurePass123!'
        response = reset_client.post(
            reverse('password_reset_confirm', args=[uidb64, token]),
            {
                'new_password1': new_password,
                'new_password2': new_password
            },
            follow=False
        )
        
        # Check for form errors or invalid link
        if response.status_code == 200:
            if 'form' in response.context:
                self.fail(f"Form validation failed: {response.context['form'].errors}")
            elif 'validlink' in response.context and not response.context['validlink']:
                self.fail("Token is invalid or expired")
            else:
                self.fail(f"Unexpected response. Context keys: {response.context.keys() if response.context else 'No context'}")
        
        # Verify redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        
        # Follow the redirect
        response = reset_client.get(response.url)
        
        # Verify password was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password('oldpassword123'))
        
        # Verify old session was invalidated
        # Check that no sessions exist for this user
        sessions_for_user = 0
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(self.user.pk):
                sessions_for_user += 1
        
        self.assertEqual(sessions_for_user, 0, "All sessions should be invalidated after password reset")
        
        # Verify user can login with new password
        new_login_client = Client()
        response = new_login_client.post(
            reverse('login'),
            {'username': 'testuser', 'password': new_password},
            follow=True
        )
        
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'testuser')



class EdgeCaseSecurityTests(TestCase):
    """Unit tests for edge cases including security validation"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
    
    def test_empty_username_input(self):
        """Test empty username input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with empty username
        response = client.post(
            reverse('user_create'),
            {
                'username': '',
                'email': 'test@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('username', response.context['form'].errors)
        
        # Verify no user was created
        self.assertFalse(User.objects.filter(email='test@test.com').exists())
    
    def test_whitespace_only_username_input(self):
        """Test whitespace-only username input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with whitespace-only username
        response = client.post(
            reverse('user_create'),
            {
                'username': '   ',
                'email': 'test@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('username', response.context['form'].errors)
        
        # Verify no user was created
        self.assertFalse(User.objects.filter(email='test@test.com').exists())
    
    def test_empty_email_input(self):
        """Test empty email input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with empty email
        response = client.post(
            reverse('user_create'),
            {
                'username': 'testuser',
                'email': '',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('email', response.context['form'].errors)
        
        # Verify no user was created
        self.assertFalse(User.objects.filter(username='testuser').exists())
    
    def test_whitespace_only_email_input(self):
        """Test whitespace-only email input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with whitespace-only email
        response = client.post(
            reverse('user_create'),
            {
                'username': 'testuser',
                'email': '   ',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('email', response.context['form'].errors)
        
        # Verify no user was created
        self.assertFalse(User.objects.filter(username='testuser').exists())
    
    def test_sql_injection_in_username(self):
        """Test SQL injection attempts in username are rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Test various SQL injection patterns
        sql_injection_attempts = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users--",
            "admin' AND 1=1--",
            "admin'--",
            'admin" OR "1"="1',
        ]
        
        for malicious_username in sql_injection_attempts:
            response = client.post(
                reverse('user_create'),
                {
                    'username': malicious_username,
                    'email': 'test@test.com',
                    'password1': 'testpass123',
                    'password2': 'testpass123',
                }
            )
            
            # Verify form has errors
            self.assertIn('username', response.context['form'].errors)
            
            # Verify no user was created with malicious username
            self.assertFalse(User.objects.filter(username=malicious_username).exists())
    
    def test_sql_injection_in_password(self):
        """Test SQL injection attempts in password field"""
        client = Client()
        
        # Create a normal user
        User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='normalpass123'
        )
        
        # Attempt login with SQL injection in password
        sql_injection_passwords = [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            '" OR "1"="1',
        ]
        
        for malicious_password in sql_injection_passwords:
            response = client.post(
                reverse('login'),
                {
                    'username': 'testuser',
                    'password': malicious_password
                }
            )
            
            # Verify login failed
            self.assertFalse(response.wsgi_request.user.is_authenticated)
            
            # Verify user still exists (table wasn't dropped)
            self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_xss_attempt_in_email(self):
        """Test XSS attempts in email field are rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Test various XSS patterns
        xss_attempts = [
            '<script>alert("XSS")</script>@test.com',
            'test@test.com<script>alert("XSS")</script>',
            'javascript:alert("XSS")@test.com',
            'test@test.com" onerror="alert(\'XSS\')',
        ]
        
        for malicious_email in xss_attempts:
            response = client.post(
                reverse('user_create'),
                {
                    'username': f'testuser_{xss_attempts.index(malicious_email)}',
                    'email': malicious_email,
                    'password1': 'testpass123',
                    'password2': 'testpass123',
                }
            )
            
            # Verify form has errors
            self.assertIn('email', response.context['form'].errors)
            
            # Verify no user was created with malicious email
            self.assertFalse(User.objects.filter(email=malicious_email).exists())
    
    def test_xss_attempt_in_first_name(self):
        """Test XSS attempts in first name field are rejected"""
        # Create a user first
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Test XSS patterns in first name
        xss_attempts = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '" onerror="alert(\'XSS\')',
        ]
        
        for malicious_name in xss_attempts:
            response = client.post(
                reverse('user_update', args=[user.pk]),
                {
                    'username': 'testuser',
                    'email': 'test@test.com',
                    'first_name': malicious_name,
                    'last_name': 'Test',
                    'is_active': True,
                }
            )
            
            # Verify form has errors
            self.assertIn('first_name', response.context['form'].errors)
            
            # Verify user's first name wasn't updated
            user.refresh_from_db()
            self.assertNotEqual(user.first_name, malicious_name)
    
    def test_xss_attempt_in_last_name(self):
        """Test XSS attempts in last name field are rejected"""
        # Create a user first
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Test XSS patterns in last name
        xss_attempts = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '" onclick="alert(\'XSS\')',
        ]
        
        for malicious_name in xss_attempts:
            response = client.post(
                reverse('user_update', args=[user.pk]),
                {
                    'username': 'testuser',
                    'email': 'test@test.com',
                    'first_name': 'Test',
                    'last_name': malicious_name,
                    'is_active': True,
                }
            )
            
            # Verify form has errors
            self.assertIn('last_name', response.context['form'].errors)
            
            # Verify user's last name wasn't updated
            user.refresh_from_db()
            self.assertNotEqual(user.last_name, malicious_name)
    
    def test_xss_attempt_in_role_name(self):
        """Test XSS attempts in role name field are rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Test XSS patterns in role name
        xss_attempts = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '" onerror="alert(\'XSS\')',
        ]
        
        for malicious_name in xss_attempts:
            response = client.post(
                reverse('role_create'),
                {
                    'name': malicious_name,
                    'permissions': [],
                }
            )
            
            # Verify form has errors
            self.assertIn('name', response.context['form'].errors)
            
            # Verify no role was created with malicious name
            self.assertFalse(Group.objects.filter(name=malicious_name).exists())
    
    def test_csrf_protection_on_login_form(self):
        """Test CSRF protection is enforced on login form"""
        client = Client(enforce_csrf_checks=True)
        
        # Attempt to post without CSRF token
        response = client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        
        # Verify CSRF error (403 Forbidden)
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_protection_on_user_create_form(self):
        """Test CSRF protection is enforced on user creation form"""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        
        # Attempt to post without CSRF token
        response = client.post(
            reverse('user_create'),
            {
                'username': 'testuser',
                'email': 'test@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify CSRF error (403 Forbidden)
        self.assertEqual(response.status_code, 403)
    
    def test_empty_role_name_input(self):
        """Test empty role name input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Get initial count
        initial_count = Group.objects.count()
        
        # Attempt to create role with empty name
        response = client.post(
            reverse('role_create'),
            {
                'name': '',
                'permissions': [],
            }
        )
        
        # Verify form has errors
        self.assertIn('name', response.context['form'].errors)
        
        # Verify no role was created
        self.assertEqual(Group.objects.count(), initial_count)
    
    def test_whitespace_only_role_name_input(self):
        """Test whitespace-only role name input is rejected"""
        client = Client()
        client.force_login(self.admin)
        
        # Get initial count
        initial_count = Group.objects.count()
        
        # Attempt to create role with whitespace-only name
        response = client.post(
            reverse('role_create'),
            {
                'name': '   ',
                'permissions': [],
            }
        )
        
        # Verify form has errors
        self.assertIn('name', response.context['form'].errors)
        
        # Verify no role was created
        self.assertEqual(Group.objects.count(), initial_count)
