<?php
/**
 * Allow Application Passwords for the local Docker demo over HTTP.
 */
add_filter('wp_is_application_passwords_available', '__return_true');
