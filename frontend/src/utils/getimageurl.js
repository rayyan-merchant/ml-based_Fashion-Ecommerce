
import { API_URL } from "../api/api";

export function getImageUrl(path) {
    if (!path) return `${API_URL}/images/placeholder.jpg`;

    // Remove leading slash
    let cleanPath = path.startsWith('/') ? path.slice(1) : path;

    // Fix for double nesting issue: if path starts with "filtered_images/", strip it.
    if (cleanPath.startsWith('filtered_images/')) {
        cleanPath = cleanPath.replace('filtered_images/', '');
    }

    // If path already starts with 'images/', don't prepend it again
    if (cleanPath.startsWith('images/')) {
        return `${API_URL}/${cleanPath}`;
    }

    return `${API_URL}/images/${cleanPath}`;
}
