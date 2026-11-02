"use client";
import {useEffect} from "react";
import {useRouter} from "next/navigation";
export default function Home(){const router=useRouter();useEffect(()=>router.replace("/dashboard/"),[router]);return <a href="/dashboard/">Open your local workspace</a>;}
