// Add this to a new file: static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Enable confirmation dialogs
    const confirmButtons = document.querySelectorAll('.confirm-action');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const message = this.dataset.confirmMessage || 'Are you sure you want to proceed?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // YouTube URL helper
    const youtubeFields = document.querySelectorAll('.youtube-url-field');
    youtubeFields.forEach(field => {
        field.addEventListener('blur', function() {
            // Convert YouTube watch URLs to embed URLs if needed
            const url = this.value;
            if (url.includes('youtube.com/watch?v=')) {
                this.value = url.replace('watch?v=', 'embed/');
            } else if (url.includes('youtu.be/')) {
                this.value = url.replace('youtu.be/', 'youtube.com/embed/');
            }
        });
    });
    
    // Initialize any tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize any popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});