// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-100">
      <SignUp 
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
      />
    </div>
  )
}