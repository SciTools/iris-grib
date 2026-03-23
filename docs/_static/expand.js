// Leaves the sidebar permanently expanded, so the whole structure is visible.
// https://github.com/readthedocs/sphinx_rtd_theme/issues/455#issuecomment-741734047
window.addEventListener('load', (_event) => {
  document.querySelectorAll(".toctree-l1").forEach(node => {
    node.classList.add("current");
  })
});