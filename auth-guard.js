/* ============================================================
   auth-guard.js · Grupo SLOTS
   Pegar en Por_Ubicacion.html y Trazabilidad.html, dentro de <head>:
       <script src="auth-guard.js"></script>
   Si no hay sesión iniciada, vuelve al Index.html (que pide el acceso).
   ============================================================ */
(function () {
  var ok = false;
  try { ok = localStorage.getItem('slots_auth_session') === 'Sistemasdeinformacion'; } catch (e) {}
  if (!ok) ok = (window.name || '').indexOf('slots-auth=1') > -1;
  if (!ok) { document.documentElement.style.display = 'none'; location.replace('Index.html'); }
})();
