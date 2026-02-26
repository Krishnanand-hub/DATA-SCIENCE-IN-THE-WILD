from flask import Blueprint, render_template, flash, redirect, url_for
portal_blueprint = Blueprint('portal', __name__, template_folder='templates')

@portal_blueprint.route("/portal")
def portal():
    return render_template("main/construction.html")