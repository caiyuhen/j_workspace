import { FormEvent, useState } from "react";

type LoginFormProps = {
  onSubmit(payload: { organizationSlug: string; userId: string }): Promise<void>;
};

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [organizationSlug, setOrganizationSlug] = useState("demo-hospital");
  const [userId, setUserId] = useState("u-001");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit({ organizationSlug, userId });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        机构标识
        <input
          aria-label="机构标识"
          value={organizationSlug}
          onChange={(event) => setOrganizationSlug(event.target.value)}
        />
      </label>
      <label>
        用户编号
        <input
          aria-label="用户编号"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
        />
      </label>
      <button type="submit">进入工作台</button>
    </form>
  );
}
