document.addEventListener('DOMContentLoaded', () => {
  // File Upload Preview
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const previewId = input.getAttribute('data-preview');
      if (file && previewId) {
        const previewElement = document.getElementById(previewId);
        if (previewElement) {
          const reader = new FileReader();
          reader.onload = (evt) => {
            previewElement.src = evt.target.result;
            previewElement.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      }
    });
  });

  // Lightbox Zoom for thumbnails
  const thumbnails = document.querySelectorAll('.img-thumb');
  thumbnails.forEach(img => {
    img.addEventListener('click', () => {
      const overlay = document.createElement('div');
      overlay.style.position = 'fixed';
      overlay.style.top = '0';
      overlay.style.left = '0';
      overlay.style.width = '100vw';
      overlay.style.height = '100vh';
      overlay.style.backgroundColor = 'rgba(7, 10, 18, 0.92)';
      overlay.style.backdropFilter = 'blur(12px)';
      overlay.style.zIndex = '2000';
      overlay.style.display = 'flex';
      overlay.style.flexDirection = 'column';
      overlay.style.alignItems = 'center';
      overlay.style.justifyContent = 'center';
      overlay.style.cursor = 'zoom-out';
      overlay.style.padding = '2rem';

      const fullImg = document.createElement('img');
      fullImg.src = img.src;
      fullImg.style.maxWidth = '90vw';
      fullImg.style.maxHeight = '85vh';
      fullImg.style.borderRadius = '16px';
      fullImg.style.boxShadow = '0 25px 50px rgba(0, 0, 0, 0.9), 0 0 40px rgba(99, 102, 241, 0.3)';

      const caption = document.createElement('div');
      caption.textContent = 'Click anywhere to close full screen view';
      caption.style.color = '#94a3b8';
      caption.style.marginTop = '1rem';
      caption.style.fontSize = '0.9rem';

      overlay.appendChild(fullImg);
      overlay.appendChild(caption);
      document.body.appendChild(overlay);

      overlay.addEventListener('click', () => {
        document.body.removeChild(overlay);
      });
    });
  });

  // Preset feedback chips for admin grading
  const feedbackTextarea = document.getElementById('feedback');
  const chips = document.querySelectorAll('.preset-chip');
  if (feedbackTextarea && chips.length > 0) {
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        const textToInsert = chip.getAttribute('data-text');
        if (feedbackTextarea.value.trim() === '') {
          feedbackTextarea.value = textToInsert;
        } else {
          feedbackTextarea.value += '\n' + textToInsert;
        }
      });
    });
  }

  // Live Search Filter for tables & card grids
  const searchInputs = document.querySelectorAll('[data-search-target]');
  searchInputs.forEach(searchInput => {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const targetSelector = searchInput.getAttribute('data-search-target');
      const items = document.querySelectorAll(targetSelector);
      
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });
});
