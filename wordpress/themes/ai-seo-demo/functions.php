<?php

function ai_seo_demo_setup(): void {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', array('search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script'));
}
add_action('after_setup_theme', 'ai_seo_demo_setup');

function ai_seo_demo_assets(): void {
    wp_enqueue_style('ai-seo-demo-style', get_stylesheet_uri(), array(), '1.0.0');
}
add_action('wp_enqueue_scripts', 'ai_seo_demo_assets');

function ai_seo_demo_excerpt_length(): int {
    return 28;
}
add_filter('excerpt_length', 'ai_seo_demo_excerpt_length');
