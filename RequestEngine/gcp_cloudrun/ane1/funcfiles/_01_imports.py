# ----------------------------------------------------
# Edge Optimizer
# Request Engine - Common Imports
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# This file contains common imports shared by all Request Engine implementations.
# It is merged with other modules during deployment.

import os
import time
import hashlib
import json
import ssl
import re
import logging
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin

import requests

# GCP-specific imports
from flask import Flask, request, jsonify
from google.cloud import secretmanager

