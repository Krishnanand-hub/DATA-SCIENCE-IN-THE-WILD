from flask import Blueprint, render_template, flash, redirect, url_for
from dataLoader import read_ons_pd
import seaborn as sns
import matplotlib.pyplot as plt
import pandas
import plotly.express as px

portal_blueprint = Blueprint('portal', __name__, template_folder='templates', static_folder='static')

@portal_blueprint.route("/portal")
def portal():
    return render_template("main/portal.html")  # EXPECTS MAP IN FIGURES