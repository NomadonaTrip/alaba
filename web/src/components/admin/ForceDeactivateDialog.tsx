"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ForceDeactivateInput } from "@/lib/validators";

interface ForceDeactivateDialogProps {
  userId: string;
  deviceId: string;
  deviceLabel: string;
  action: (
    userId: string,
    deviceId: string,
    input: ForceDeactivateInput
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function ForceDeactivateDialog({
  userId,
  deviceId,
  deviceLabel,
  action,
}: ForceDeactivateDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [serverErr, setServerErr] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<ForceDeactivateInput>({
    resolver: zodResolver(ForceDeactivateInput),
  });

  const onSubmit = handleSubmit(async (data) => {
    setServerErr(null);
    const result = await action(userId, deviceId, data);
    if (!result.ok) {
      setServerErr(result.error ?? "Server error");
      return;
    }
    setOpen(false);
    router.refresh();
  });

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Force deactivate
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Force-deactivate device?</DialogTitle>
            <DialogDescription>
              <strong>{deviceLabel}</strong> will be deactivated immediately,
              bypassing the user&apos;s 90-day cooldown. Downloaded films on this device
              will continue to play until the device is reset, but the user cannot
              re-authenticate on it.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="reason">
                Reason for the audit log <span className="text-red-600">*</span>
              </Label>
              <Textarea
                id="reason"
                placeholder="e.g. User reported phone stolen via support ticket #234"
                rows={3}
                {...register("reason")}
              />
              {errors.reason && (
                <p className="text-xs text-red-600">{errors.reason.message}</p>
              )}
              {serverErr && <p className="text-xs text-red-600">{serverErr}</p>}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="destructive" disabled={isSubmitting}>
                {isSubmitting ? "Deactivating..." : "Force deactivate"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
