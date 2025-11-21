from functools import wraps
from flask import session, redirect, flash

def role_required(*roles):
	def wrapper(fn):
		@wraps(fn)
		def decorated_view(*args, **kwargs):
			if session.get("role") not in roles:
				flash("You don’t have permission to view this page.")
				return redirect("/")
			return fn(*args, **kwargs)
		return decorated_view
	return wrapper
