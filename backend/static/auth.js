function checkAccess(allowedRoles) {
    const raw = localStorage.getItem("user_info");

    // ❌ User not logged in
    if (!raw) {
        Swal.fire({
            icon: 'warning',
            title: 'Not Logged In',
            text: 'Please log in to continue.',
            confirmButtonText: 'Go to Login'
        }).then(() => {
            window.location.href = "/login";
        });
        return;
    }

    const user = JSON.parse(raw);

    // ❌ Role does not match (Unauthorized)
    if (!allowedRoles.includes(user.role)) {
        Swal.fire({
            icon: 'error',
            title: 'Access Denied',
            text: 'You do not have permission to view this page.',
            confirmButtonText: 'Back'
        }).then(() => {
            window.location.href = "/login";
        });
        return;
    }

    // ✅ Access allowed (nothing happens)
}
