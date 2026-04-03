// Copy share link to clipboard
function copyShareLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        alert('Share link copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy link. Please copy manually: ' + url);
    });
}
