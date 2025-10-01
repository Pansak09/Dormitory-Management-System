def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_tenant(user):
    return user.is_authenticated and user.groups.filter(name="Tenant").exists()

def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)
