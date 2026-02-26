function applyScale() {
  const container = document.querySelector('.scalable-viewport');
  const content = document.querySelector('.scalable-content');
  if (!container || !content) return;
  const cw = content.offsetWidth;
  const ch = content.offsetHeight;
  const vw = container.clientWidth;
  const vh = container.clientHeight;
  const scale = Math.min(vw / cw, vh / ch);
  content.style.transform = 'scale(' + scale + ')';
}

window.addEventListener('resize', applyScale);
window.addEventListener('DOMContentLoaded', function(){ applyScale(); setTimeout(applyScale,300); });
