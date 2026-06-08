import { useEffect, useState } from "react";

import { api, type CurrentUser, type UpdateMePayload } from "../lib/api";
import {
  getUI,
  localeLabel,
  localeText,
  SUPPORTED_LOCALES,
  type Locale,
} from "../lib/i18n";

function displayNameStorageKey(userId?: string | null) {
  return userId ? `fastoj.displayName.${userId}` : null;
}

function displayNameForUser(user?: Pick<CurrentUser, "id" | "username"> | null) {
  const key = displayNameStorageKey(user?.id);
  const saved = key ? localStorage.getItem(key)?.trim() : "";
  return saved || user?.username || "FastOJ User";
}

function saveDisplayNameForUser(user: Pick<CurrentUser, "id"> | null | undefined, displayName: string) {
  const key = displayNameStorageKey(user?.id);
  if (!key) return;
  const trimmed = displayName.trim();
  if (trimmed) {
    localStorage.setItem(key, trimmed);
  } else {
    localStorage.removeItem(key);
  }
}

function localizedAuthError(message: string, text: ReturnType<typeof getUI>) {
  const normalized = message.trim();
  if (!normalized) return text.authFailure;
  if (normalized === "Login failed" || normalized === "Incorrect username or password") {
    return text.authInvalidCredentials;
  }
  if (normalized === "Username or email already registered") {
    return text.authAlreadyRegistered;
  }
  if (normalized.startsWith("Validation failed:")) {
    return text.authInvalidFields;
  }
  return normalized;
}

export function AuthPage({
  mode,
  locale,
  onMode,
  onDone,
}: {
  mode: "login" | "register";
  locale: Locale;
  onMode: (mode: "login" | "register") => void;
  onDone: () => void;
}) {
  const text = getUI(locale);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string>(text.authMessage);
  const [dialog, setDialog] = useState<{ title: string; message: string; tone: "error" | "success"; onConfirm?: () => void } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setMessage(text.authMessage);
  }, [text.authMessage]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (mode === "register" && password !== confirmPassword) {
      setMessage(text.passwordMismatch);
      setDialog({ title: text.authDialogTitle, message: text.passwordMismatch, tone: "error" });
      return;
    }
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(username, email, password, locale);
      }
      await api.login(username, password);
      setMessage(text.authSuccess);
      if (mode === "register") {
        setDialog({
          title: text.registerSuccessTitle,
          message: text.registerSuccessMessage,
          tone: "success",
          onConfirm: onDone,
        });
      } else {
        onDone();
      }
    } catch (error) {
      const errorMessage = localizedAuthError(error instanceof Error ? error.message : "", text);
      setMessage(errorMessage);
      setDialog({ title: text.authDialogTitle, message: errorMessage, tone: "error" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-copy">
          <p className="eyebrow">{localeText(locale, { zh: "FastOJ 账号", en: "FastOJ Account" })}</p>
          <h1>{text.authPanelTitle}</h1>
          <p>{text.accountCopy}</p>
          <div className="auth-proof">
            <span>{localeText(locale, { zh: "题库练习", en: "Problem practice" })}</span>
            <span>{localeText(locale, { zh: "智能反馈", en: "Smart feedback" })}</span>
            <span>{localeText(locale, { zh: "公平评测", en: "Fair judging" })}</span>
          </div>
        </div>
        <form className="auth-form" onSubmit={submit} autoComplete="off">
          <div className="auth-tabs" role="tablist" aria-label={localeText(locale, { zh: "认证方式", en: "Authentication mode" })}>
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => onMode("login")}>{text.login}</button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => onMode("register")}>{text.register}</button>
          </div>
          <label>{text.username}<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="off" /></label>
          {mode === "register" ? <label>{text.email}<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="off" /></label> : null}
          <label>{text.password}<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="off" /></label>
          {mode === "login" ? (
            <p className="muted">
              {localeText(locale, {
                zh: "忘记密码请联系管理员重置。",
                en: "Forgot your password? Ask an administrator to reset it.",
              })}
            </p>
          ) : null}
          {mode === "register" ? <label>{text.confirmPassword}<input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} type="password" autoComplete="off" /></label> : null}
          <button className="primary auth-submit" disabled={busy}>
            {busy ? text.processing : mode === "login" ? text.loginContinue : text.registerContinue}
          </button>
          <p className="muted">{message}</p>
        </form>
        {dialog ? (
          <div className="auth-dialog-backdrop" role="presentation">
            <div className={`auth-dialog ${dialog.tone}`} role="alertdialog" aria-modal="true" aria-labelledby="auth-dialog-title">
              <h2 id="auth-dialog-title">{dialog.title}</h2>
              <p>{dialog.message}</p>
              <button
                type="button"
                className="primary"
                onClick={() => {
                  const onConfirm = dialog.onConfirm;
                  setDialog(null);
                  onConfirm?.();
                }}
              >
                {text.dialogConfirm}
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}

export function SettingsPage({
  locale,
  currentUser,
  theme,
  onTheme,
  onLocaleChange,
  onClose,
  onProfileSaved,
}: {
  locale: Locale;
  currentUser: CurrentUser | null;
  theme: "light" | "dark";
  onTheme: (theme: "light" | "dark") => void;
  onLocaleChange: (locale: Locale) => void;
  onClose: () => void;
  onProfileSaved: (user: CurrentUser) => void;
}) {
  const text = getUI(locale);
  const [displayName, setDisplayName] = useState(() => displayNameForUser(currentUser));
  const [username, setUsername] = useState(currentUser?.username ?? "");
  const [email, setEmail] = useState(currentUser?.email ?? "");
  const [avatarUrl, setAvatarUrl] = useState(currentUser?.avatar_url ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [compact, setCompact] = useState(localStorage.getItem("fastoj.compactMode") === "true");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    setDisplayName(displayNameForUser(currentUser));
    setUsername(currentUser?.username ?? "");
    setEmail(currentUser?.email ?? "");
    setAvatarUrl(currentUser?.avatar_url ?? "");
  }, [currentUser?.id, currentUser?.username, currentUser?.email, currentUser?.avatar_url]);

  async function save() {
    localStorage.setItem("fastoj.compactMode", String(compact));
    const payload: UpdateMePayload = {
      username: username.trim(),
      email: email.trim(),
      avatar_url: avatarUrl.trim() || null,
      locale,
    };
    if (newPassword) {
      payload.current_password = currentPassword;
      payload.new_password = newPassword;
    }
    try {
      const updated = await api.updateMe(payload);
      saveDisplayNameForUser(updated, displayName);
      onProfileSaved(updated);
      setCurrentPassword("");
      setNewPassword("");
      setSaved(localeText(locale, { zh: "已保存。", en: "Saved." }));
    } catch (error) {
      setSaved(error instanceof Error ? error.message : localeText(locale, { zh: "保存失败。", en: "Save failed." }));
    }
  }

  return (
    <main className="settings-page">
      <section className="settings-card account-card">
        <button className="icon-button close-button tip" data-tip={localeText(locale, { zh: "关闭", en: "Close" })} onClick={onClose}>
          <span className="icon-glyph" aria-hidden="true">x</span>
        </button>
        <p className="eyebrow">{localeText(locale, { zh: "账号", en: "Account" })}</p>
        <h1>{text.settingsTitle}</h1>
        <p className="muted">{text.settingsCopy}</p>
        <div className="account-profile">
          <div className="avatar-preview">{avatarUrl ? <img src={avatarUrl} alt="" /> : (displayName.trim() || username || "F").slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{displayName.trim() || username || "FastOJ User"}</strong>
            <span>{currentUser?.role === "admin" ? localeText(locale, { zh: "管理员", en: "Admin" }) : localeText(locale, { zh: "用户", en: "User" })}</span>
          </div>
        </div>
        <div className="settings-grid">
          <label>{text.displayName}<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label>
          <label>{text.username}<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
          <label>{text.email}<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" /></label>
          <label>{localeText(locale, { zh: "头像 URL", en: "Avatar URL" })}<input value={avatarUrl} onChange={(event) => setAvatarUrl(event.target.value)} /></label>
          <label>{localeText(locale, { zh: "当前密码", en: "Current password" })}<input value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} type="password" autoComplete="current-password" /></label>
          <label>{localeText(locale, { zh: "新密码", en: "New password" })}<input value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" autoComplete="new-password" /></label>
        </div>
        <label className="toggle-row">
          <input type="checkbox" checked={compact} onChange={(event) => setCompact(event.target.checked)} />
          {text.compactMode}
        </label>
        <div className="theme-settings">
          <span>{localeText(locale, { zh: "界面语言", en: "Interface language" })}</span>
          <div className="segmented theme-segmented" role="group" aria-label={localeText(locale, { zh: "界面语言", en: "Interface language" })}>
            {SUPPORTED_LOCALES.map((item) => (
              <button type="button" key={item} className={locale === item ? "active" : ""} aria-pressed={locale === item} onClick={() => onLocaleChange(item)}>
                {localeLabel(item)}
              </button>
            ))}
          </div>
        </div>
        <div className="theme-settings">
          <span>{localeText(locale, { zh: "界面主题", en: "Theme" })}</span>
          <div className="segmented theme-segmented" role="group" aria-label={localeText(locale, { zh: "界面主题", en: "Theme" })}>
            <button type="button" className={theme === "light" ? "active" : ""} aria-pressed={theme === "light"} onClick={() => onTheme("light")}>
              {localeText(locale, { zh: "浅色", en: "Light" })}
            </button>
            <button type="button" className={theme === "dark" ? "active" : ""} aria-pressed={theme === "dark"} onClick={() => onTheme("dark")}>
              {localeText(locale, { zh: "深色", en: "Dark" })}
            </button>
          </div>
        </div>
        <button className="primary" onClick={save}>{text.saveSettings}</button>
        {saved ? <p className="muted">{saved}</p> : null}
      </section>
    </main>
  );
}
