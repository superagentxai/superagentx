permit (
    principal is User,
    action == Action::"RunTask",
    resource is Service
)
when {
    principal.status == "Active" &&
    context.depth <= 5
};