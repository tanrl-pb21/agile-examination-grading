// auth.js
window.checkAccess = function(allowedRoles) {
    const raw = localStorage.getItem("user_info");
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
}

window.updateSidebarUserInfo = function() {
    const userInfo = JSON.parse(localStorage.getItem("user_info"));
    if (!userInfo) return;

    const emailEl = document.querySelector(".user-info p");
    if (emailEl) emailEl.textContent = userInfo.email;

    const roleEl = document.querySelector(".user-info h4");
    if (roleEl && userInfo.role) {
        roleEl.textContent =
            userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1);
    }

    const avatarEl = document.querySelector(".user-avatar");
    if (avatarEl) {
        const initial = userInfo.email
            ? userInfo.email.charAt(0).toUpperCase()
            : "U";
        avatarEl.textContent = initial;
    }

}

function handleLogout() {
    Swal.fire({
        icon: 'question',
        title: 'Confirm Logout',
        text: 'Are you sure you want to log out?',
        showCancelButton: true,
        confirmButtonText: 'Logout',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#dc2626'
    }).then((result) => {
        if (result.isConfirmed) {
            localStorage.removeItem("user_info");
            localStorage.removeItem("access_token");

            Swal.fire({
                icon: 'success',
                title: 'Logged Out',
                text: 'You have been logged out successfully.',
                timer: 1200,
                showConfirmButton: false
            }).then(() => {
                window.location.href = "/login";
            });
        }
    });
}
