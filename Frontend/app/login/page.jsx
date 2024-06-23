'use client';

import React, { useState } from "react";
import { Cookies } from "react-cookie";
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation";

const Login = () => {
  const [email, setEmail] = useState('');
  const cookies = new Cookies();
  const router = useRouter();

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handelButton = () => {
    cookies.set('email',email);
    router.push("/mypage")
  }

  return (
    <div className="container max-w-sm items-center jusitfy-center">
    <div className="flex flex-col gap-3 items-center justify-center">
      <h2 className="text-xl font-semibold">로그인</h2>
      <form className="flex flex-col gap-5">
        <div className="flex flex-row gap-3 items-center justify-center">
          <label htmlFor="email">Email</label>
          <Input
            type="email"
            id="email"
            value={email}
            placeholder={"이메일 입력해주세요"}
            onChange={handleEmailChange}
          />
        </div>
        <Button onClick={handelButton} type="submit">Login</Button>
      </form>
    </div>
    </div>
  );
};

export default Login;
